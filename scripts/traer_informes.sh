#!/usr/bin/env bash
# =============================================================================
# traer_informes.sh — Informes de visitas del SERVIDOR, en una sola orden
# =============================================================================
# Genera los informes en el servidor, se los trae y abre el que toque.
#
# POR QUÉ EXISTE. Los informes viven en el servidor y no se publican: llevan las
# direcciones IP de los visitantes, así que dejarlos donde Nginx los sirva sería
# exponer datos de la gente. Eso obligaba a encadenar a mano un `ssh`, un `scp`
# y abrir el fichero, cada vez.
#
# LA DISTINCIÓN QUE IMPORTA. `informes/` guarda los informes LOCALES, sacados de
# los registros del Docker de desarrollo: son tu propio trasteo, no visitas.
# Este script deja los del servidor en `informes/servidor/`, separados, para que
# no se confunda el tráfico real con el de uno mismo.
#
# Uso:
#   make informes              → últimos 7 días, resumen en español
#   make informes DIAS=30      → otro periodo
#   make informes TIPO=goaccess → informe completo de GoAccess
#   make informes ABRIR=no     → solo descargar, sin abrir el navegador
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

SERVIDOR="${SERVIDOR:-servidor}"
RUTA_REMOTA="${RUTA_REMOTA:-/opt/subvdgda}"
DIAS="${DIAS:-7}"
TIPO="${TIPO:-resumen}"
ABRIR="${ABRIR:-si}"
DESTINO="informes/servidor"

if [ -t 1 ]; then VERDE="\033[0;32m"; AMARILLO="\033[1;33m"; RESET="\033[0m"
else VERDE=""; AMARILLO=""; RESET=""; fi

mkdir -p "$DESTINO"

# ── Una sola conexión para todo ──────────────────────────────────────────────
# Sin esto, el `ssh` que genera el informe y el `scp` que se lo trae abren
# sesiones distintas y la clave pide la contraseña dos veces. Mismo apaño que en
# traer_copias.sh: se abre un canal y se reutiliza. El socket va a un temporal
# propio y un `trap` lo cierra pase lo que pase.
CANAL=$(mktemp -u "${TMPDIR:-/tmp}/subvdgda-ssh-XXXXXX")
SSH_OPTS=(-o ControlMaster=auto -o ControlPath="$CANAL" -o ControlPersist=30)
cerrar_canal() {
    ssh -o ControlPath="$CANAL" -O exit "$SERVIDOR" 2>/dev/null || true
    rm -f "$CANAL"
}
trap cerrar_canal EXIT

# ── 1. Generar en el servidor ────────────────────────────────────────────────
echo "Generando el informe en $SERVIDOR (te pedirá la contraseña de la clave)..."

if [ "$TIPO" = "goaccess" ]; then
    # GoAccess da el detalle: navegadores, dispositivos, códigos de error.
    ssh "${SSH_OPTS[@]}" "$SERVIDOR" "cd $RUTA_REMOTA && bash scripts/informe_visitas.sh" \
        || { echo "No se pudo generar. ¿Está GoAccess instalado en el servidor? (apt install goaccess)"; exit 1; }
    PATRON="visitas-*.html"
else
    # El resumen en español lleva el periodo en el nombre para que dos
    # ejecuciones con distintos días no se pisen, que es lo que pasaba antes.
    ssh "${SSH_OPTS[@]}" "$SERVIDOR" "cd $RUTA_REMOTA && python3 scripts/resumen_visitas.py --dias $DIAS"
    PATRON="resumen-*.html"
fi

# ── 2. Traérselos ────────────────────────────────────────────────────────────
echo "Descargando a $DESTINO/ ..."
scp -q "${SSH_OPTS[@]}" "$SERVIDOR:$RUTA_REMOTA/informes/$PATRON" "$DESTINO/"

ULTIMO=$(ls -t "$DESTINO"/$PATRON 2>/dev/null | head -1)
if [ -z "$ULTIMO" ]; then
    echo "No se descargó ningún informe. Revisa $RUTA_REMOTA/informes/ en el servidor."
    exit 1
fi

# Traerse también el histórico del servidor, que allí se mantiene por tarea
# programada. Sin esto, un mes sin mirar el correo y sin descargar nada dejaría
# huecos aunque el servidor los tuviera bien guardados. Se fusiona con el local
# quedándose con el valor mayor de cada día, así que da igual cuál vaya por
# delante.
if scp -q "${SSH_OPTS[@]}" "$SERVIDOR:$RUTA_REMOTA/informes/historico.json" \
        "$DESTINO/historico-servidor.json" 2>/dev/null; then
    python3 - "$DESTINO/historico-servidor.json" <<'FIN' || true
import json, sys
from pathlib import Path
remoto = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
local_p = Path("informes/historico.json")
local = json.loads(local_p.read_text(encoding="utf-8")) if local_p.exists() else {"dias": {}, "periodos": []}
antes = len(local["dias"])
for d, n in remoto.get("dias", {}).items():
    local["dias"][d] = max(local["dias"].get(d, 0), n)
ya = {(p.get("desde"), p.get("hasta")) for p in local["periodos"]}
for p in remoto.get("periodos", []):
    if (p.get("desde"), p.get("hasta")) not in ya:
        local["periodos"].append(p)
local["dias"] = dict(sorted(local["dias"].items()))
local["periodos"].sort(key=lambda p: p.get("desde") or "")
local_p.write_text(json.dumps(local, ensure_ascii=False, indent=2), encoding="utf-8")
ganados = len(local["dias"]) - antes
print(f"Histórico del servidor incorporado: {'+' + str(ganados) if ganados else 'sin días nuevos'}.")
FIN
    rm -f "$DESTINO/historico-servidor.json"
fi

# Alimentar el histórico con el informe recién descargado. Los registros del
# servidor se borran a los 30 días, así que cada informe es la única ocasión de
# conservar esos días. Si falla, no se corta: el informe ya está.
if [ "$TIPO" != "goaccess" ]; then
    python3 scripts/historico_visitas.py "$ULTIMO" >/dev/null 2>&1 \
        && echo "Histórico de visitas actualizado (make evolucion para verlo)." \
        || echo "Aviso: no se pudo actualizar el histórico."
fi

echo -e "${VERDE}Listo:${RESET} $ULTIMO"
echo -e "${AMARILLO}Contiene direcciones IP: no lo subas a ningún sitio público.${RESET}"

# ── 3. Abrirlo ───────────────────────────────────────────────────────────────
# En WSL hay que traducir la ruta al formato de Windows: el navegador es una
# aplicación de Windows y no entiende las rutas de Linux.
# Se prefiere Chrome al navegador predeterminado: en esta máquina el
# predeterminado es Edge y los informes se revisan en Chrome. Con
# NAVEGADOR=predeterminado se vuelve al de siempre, y con NAVEGADOR=/ruta.exe
# se usa otro.
buscar_chrome() {
    case "${NAVEGADOR:-}" in
        predeterminado) return 1 ;;
        "" | chrome) ;;
        *) echo "$NAVEGADOR"; return 0 ;;
    esac
    for c in "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
             "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"; do
        [ -f "$c" ] && { echo "$c"; return 0; }
    done
    return 1
}

if [ "$ABRIR" = "si" ]; then
    if command -v wslpath >/dev/null 2>&1; then
        RUTA_WIN=$(wslpath -w "$ULTIMO")
        if NAVEG=$(buscar_chrome); then
            "$NAVEG" "$RUTA_WIN" >/dev/null 2>&1 &
            echo "Abriendo en Chrome..."
        elif command -v explorer.exe >/dev/null 2>&1; then
            # explorer.exe devuelve código 1 aunque abra bien, así que se ignora.
            explorer.exe "$RUTA_WIN" 2>/dev/null || true
            echo "Abriendo en el navegador predeterminado..."
        else
            echo "Ábrelo a mano: $ULTIMO"
        fi
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$ULTIMO" >/dev/null 2>&1 &
    else
        echo "Ábrelo a mano: $ULTIMO"
    fi
fi
