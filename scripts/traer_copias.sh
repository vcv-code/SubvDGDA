#!/usr/bin/env bash
# =============================================================================
# traer_copias.sh — Copias de seguridad del SERVIDOR, en una sola orden
# =============================================================================
# POR QUÉ EXISTE. Las copias programadas viven en la MISMA máquina que la base
# de datos, así que no protegen del único fallo que importa de verdad: perder la
# máquina. Traérselas era un paso manual —ssh, ls, scp con el nombre exacto— y
# lo que hay que acordarse de hacer no se hace: entre agosto y septiembre de
# 2026 no se bajó ninguna.
#
# QUÉ SE PIERDE SI SE PIERDE EL SERVIDOR. El dataset se puede reconstruir desde
# el BOE, pero no todo está ahí: las cuentas de usuario, los avisos publicados y
# las fechas de fin de plazo se meten a mano y no existen en ninguna otra parte.
#
# Uso:
#   make copias                → trae la más reciente que no tengamos
#   make copias TODAS=si       → trae todas las que falten
#   make copias LISTAR=si      → solo mirar qué hay en el servidor, sin bajar
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

SERVIDOR="${SERVIDOR:-servidor}"
RUTA_REMOTA="${RUTA_REMOTA:-/opt/subvdgda}"
TODAS="${TODAS:-no}"
LISTAR="${LISTAR:-no}"
DESTINO="backups/servidor"

if [ -t 1 ]; then VERDE="\033[0;32m"; AMARILLO="\033[1;33m"; RESET="\033[0m"
else VERDE=""; AMARILLO=""; RESET=""; fi

# Carpeta aparte de backups/, igual que informes/servidor/: confundir una copia
# del servidor con una local lleva a restaurar la equivocada, que es de los
# errores más caros que se pueden cometer aquí.
mkdir -p "$DESTINO"

# ── Una sola conexión para todo ──────────────────────────────────────────────
# Sin esto, cada `ssh` y cada `scp` abren su propia sesión y la clave pide la
# contraseña OTRA VEZ: traerse seis copias eran siete peticiones seguidas.
# ControlMaster abre un canal y lo reutiliza; ControlPersist lo deja vivo unos
# segundos entre órdenes. El socket va a un fichero temporal propio y se cierra
# al terminar, pase lo que pase.
CANAL=$(mktemp -u "${TMPDIR:-/tmp}/subvdgda-ssh-XXXXXX")
SSH_OPTS=(-o ControlMaster=auto -o ControlPath="$CANAL" -o ControlPersist=30)
cerrar_canal() {
    ssh -o ControlPath="$CANAL" -O exit "$SERVIDOR" 2>/dev/null || true
    rm -f "$CANAL"
}
trap cerrar_canal EXIT

# ── 1. Ver qué hay en el servidor ────────────────────────────────────────────
echo "Consultando $SERVIDOR (te pedirá la contraseña de la clave)..."
if ! REMOTAS=$(ssh "${SSH_OPTS[@]}" "$SERVIDOR" "ls -1 $RUTA_REMOTA/backups/backup_*.sql 2>/dev/null | sort"); then
    echo "No se pudo conectar con $SERVIDOR." >&2
    echo "Comprueba el alias en ~/.ssh/config y que la clave sea la correcta." >&2
    exit 1
fi

if [ -z "$REMOTAS" ]; then
    echo "Conecta bien, pero no hay ninguna copia en $RUTA_REMOTA/backups/."
    echo "¿Está programada la tarea? Revísalo con: ssh $SERVIDOR 'crontab -l'"
    exit 1
fi

echo "En el servidor hay $(echo "$REMOTAS" | wc -l) copia(s):"
echo "$REMOTAS" | xargs -n1 basename | sed 's/^/   /'

if [ "$LISTAR" = "si" ]; then exit 0; fi

# ── 2. Bajar solo lo que falte ───────────────────────────────────────────────
# Se comparan por nombre, que lleva la fecha y la hora. Volver a bajar una copia
# que ya está no rompe nada, pero son ~800 KB cada una y el enlace es el de casa.
if [ "$TODAS" = "si" ]; then
    CANDIDATAS="$REMOTAS"
else
    CANDIDATAS=$(echo "$REMOTAS" | tail -1)
fi

NUEVAS=()
while IFS= read -r remota; do
    [ -n "$remota" ] || continue
    nombre=$(basename "$remota")
    if [ -f "$DESTINO/$nombre" ]; then
        echo "   ya la tienes: $nombre"
        continue
    fi
    echo "   descargando $nombre ..."
    scp -q "${SSH_OPTS[@]}" "$SERVIDOR:$remota" "$DESTINO/"
    NUEVAS+=("$DESTINO/$nombre")
done <<< "$CANDIDATAS"

BAJADAS=${#NUEVAS[@]}
if [ "$BAJADAS" -eq 0 ]; then
    echo -e "${VERDE}Al día:${RESET} no había nada nuevo que traer."
    exit 0
fi

# ── 3. Comprobar que el volcado no viene truncado ────────────────────────────
# Un volcado cortado a medias restaura una base de datos incompleta, que es peor
# que no tener copia: parece que funciona. mysqldump cierra siempre con esa
# marca, así que su ausencia delata el corte. Lo mismo que comprueba `make
# restore` antes de tocar nada.
#
# Se comprueban exactamente las que se acaban de bajar, anotadas al descargarlas:
# deducirlas por fecha de modificación funcionaba, pero se apoyaba en que `scp`
# les pone la hora actual, que es un detalle que puede cambiar.
echo
PROBLEMAS=0
for f in "${NUEVAS[@]}"; do
    if [ ! -s "$f" ]; then
        PROBLEMAS=$((PROBLEMAS + 1))
        printf "   %-44s %8s  ${AMARILLO}VACÍA — el volcado falló en el servidor${RESET}\n" \
            "$(basename "$f")" "0"
    elif tail -5 "$f" | grep -q "Dump completed"; then
        printf "   %-44s %8s  ${VERDE}íntegra${RESET}\n" "$(basename "$f")" "$(du -h "$f" | cut -f1)"
    else
        PROBLEMAS=$((PROBLEMAS + 1))
        printf "   %-44s %8s  ${AMARILLO}SIN MARCA DE CIERRE — no la uses${RESET}\n" \
            "$(basename "$f")" "$(du -h "$f" | cut -f1)"
    fi
done

# Sin esto, quien lance el modo por defecto y se encuentre la última copia rota
# se queda sin saber que hay anteriores que sí sirven.
if [ "$PROBLEMAS" -gt 0 ] && [ "$TODAS" != "si" ]; then
    echo
    echo -e "${AMARILLO}La copia más reciente no sirve.${RESET} Lanza 'make copias TODAS=si'"
    echo "para traerte también las anteriores y quedarte con la última que esté íntegra."
fi

echo
echo -e "${VERDE}Listo:${RESET} $BAJADAS copia(s) nueva(s) en $DESTINO/"
echo -e "${AMARILLO}Llevan datos personales de las cuentas: no las subas a ningún sitio.${RESET}"
echo "Para restaurar una: make restore FILE=$DESTINO/backup_AAAAMMDD_HHMMSS.sql"
