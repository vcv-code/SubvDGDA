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

# ── 1. Generar en el servidor ────────────────────────────────────────────────
echo "Generando el informe en $SERVIDOR (te pedirá la contraseña de la clave)..."

if [ "$TIPO" = "goaccess" ]; then
    # GoAccess da el detalle: navegadores, dispositivos, códigos de error.
    ssh "$SERVIDOR" "cd $RUTA_REMOTA && bash scripts/informe_visitas.sh" \
        || { echo "No se pudo generar. ¿Está GoAccess instalado en el servidor? (apt install goaccess)"; exit 1; }
    PATRON="visitas-*.html"
else
    # El resumen en español lleva el periodo en el nombre para que dos
    # ejecuciones con distintos días no se pisen, que es lo que pasaba antes.
    ssh "$SERVIDOR" "cd $RUTA_REMOTA && python3 scripts/resumen_visitas.py --dias $DIAS"
    PATRON="resumen-*.html"
fi

# ── 2. Traérselos ────────────────────────────────────────────────────────────
echo "Descargando a $DESTINO/ ..."
scp -q "$SERVIDOR:$RUTA_REMOTA/informes/$PATRON" "$DESTINO/"

ULTIMO=$(ls -t "$DESTINO"/$PATRON 2>/dev/null | head -1)
if [ -z "$ULTIMO" ]; then
    echo "No se descargó ningún informe. Revisa $RUTA_REMOTA/informes/ en el servidor."
    exit 1
fi

echo -e "${VERDE}Listo:${RESET} $ULTIMO"
echo -e "${AMARILLO}Contiene direcciones IP: no lo subas a ningún sitio público.${RESET}"

# ── 3. Abrirlo ───────────────────────────────────────────────────────────────
# En WSL hay que traducir la ruta al formato de Windows: el navegador es una
# aplicación de Windows y no entiende las rutas de Linux.
if [ "$ABRIR" = "si" ]; then
    if command -v wslpath >/dev/null 2>&1 && command -v explorer.exe >/dev/null 2>&1; then
        # explorer.exe devuelve código 1 aunque abra bien, así que se ignora.
        explorer.exe "$(wslpath -w "$ULTIMO")" 2>/dev/null || true
        echo "Abriendo en el navegador..."
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$ULTIMO" >/dev/null 2>&1 &
    else
        echo "Ábrelo a mano: $ULTIMO"
    fi
fi
