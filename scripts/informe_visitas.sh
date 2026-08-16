#!/usr/bin/env bash
# =============================================================================
# informe_visitas.sh — Informe HTML de visitas a partir de los logs de Nginx
# =============================================================================
# Genera un informe con GoAccess: páginas más vistas, de dónde llega la gente,
# navegadores y dispositivos, códigos de error y tiempos de respuesta.
#
# NO usa servicios externos ni cookies. Todo sale de los registros que Nginx ya
# escribe y que `privacidad.html` declara en "Registros del servidor".
#
# El informe NO se publica: se escribe en `informes/`, fuera de la carpeta que
# Nginx sirve. Contiene direcciones IP, así que dejarlo accesible en la web
# sería exponer datos de los visitantes.
#
# Requiere GoAccess en el sistema anfitrión:
#     apt install goaccess
#
# Uso:
#   scripts/informe_visitas.sh                    → informe + rotación
#   INFORMES_DIAS=30 scripts/informe_visitas.sh   → conservar solo 30 días
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

LOG_DIR="logs/nginx"
DESTINO="informes"
ENV_FILE="docker/.env"

if ! command -v goaccess >/dev/null 2>&1; then
    echo "ERROR: falta goaccess. Instálalo con 'apt install goaccess'." >&2
    exit 1
fi

# El .env es opcional aquí: este script no necesita credenciales, solo permite
# fijar la retención en el mismo sitio que la de las copias de seguridad.
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    set -a; . "$ENV_FILE"; set +a
fi

# Igual que en backup_db.sh, la configuración se lee DESPUÉS del .env para que
# valga tanto para la tarea programada como para una ejecución a mano.
INFORMES_DIAS="${INFORMES_DIAS:-365}"

# Formato de log: es el de `docker/nginx/default.conf` (log_format bdns), que
# es COMBINED más $request_time al final.
#
# Importante: GoAccess acepta también --log-format=COMBINED sobre estas líneas
# sin quejarse, pero entonces IGNORA el tiempo de respuesta y el informe pierde
# la sección de páginas lentas. Por eso se declara explícitamente, con %T.
#
# Si algún día se cambia el log_format de Nginx, hay que cambiarlo aquí.
FORMATO='%h %^[%d:%t %^] "%r" %s %b "%R" "%u" %T'

mkdir -p "$DESTINO"

# Se leen también los rotados (access.log.YYYY-MM-DD, que crea rotar_logs.py):
# sin ellos el informe solo cubriría desde la última rotación, no los 30 días.
mapfile -t LOGS < <(ls -1 "$LOG_DIR"/access.log "$LOG_DIR"/access.log.* 2>/dev/null || true)

if [ ${#LOGS[@]} -eq 0 ]; then
    echo "ERROR: no hay registros en $LOG_DIR." >&2
    exit 1
fi

FECHA="$(date +%F)"
SALIDA="$DESTINO/visitas-$FECHA.html"

# --ignore-crawlers descuenta los rastreadores conocidos (Google, Bing...) del
# recuento de visitantes. En una web nueva son la mayor parte del tráfico, y sin
# filtrarlos las cifras engañan.
# --num-tests=0 desactiva la comprobación inicial de formato, que aborta el
# informe entero si las primeras líneas no encajan. Un registro real SIEMPRE
# tiene líneas sueltas que no casan: peticiones malformadas de bots, sondas de
# escaneo, y aquí además líneas heredadas de un log_format anterior. Sin esto,
# una sola línea rara al principio deja a la web sin informe. Las líneas que no
# encajan se saltan; la comprobación de más abajo avisa si NINGUNA encaja.
goaccess "${LOGS[@]}" \
    --log-format="$FORMATO" \
    --date-format='%d/%b/%Y' \
    --time-format='%H:%M:%S' \
    --ignore-crawlers \
    --num-tests=0 \
    --html-report-title="Visitas — subvencionesdgda.org ($FECHA)" \
    --output="$SALIDA"

# GoAccess devuelve 0 aunque no parsee ni una línea: en ese caso escribe un
# informe con la estructura completa y todos los contadores a cero. Comprobarlo
# aquí evita descubrir semanas después que el formato dejó de encajar.
VALIDAS="$(goaccess "${LOGS[@]}" \
    --log-format="$FORMATO" --date-format='%d/%b/%Y' --time-format='%H:%M:%S' \
    --num-tests=0 --output=json 2>/dev/null \
    | grep -oE '"valid_requests":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+')"

if [ -z "${VALIDAS:-}" ] || [ "$VALIDAS" -eq 0 ]; then
    echo "ERROR: GoAccess no ha reconocido ninguna línea. El log_format de Nginx" >&2
    echo "       y el FORMATO de este script ya no coinciden." >&2
    rm -f "$SALIDA"
    exit 1
fi

echo "Informe generado: $SALIDA ($VALIDAS peticiones)"

# Rotación, igual que las copias de seguridad
BORRADOS="$(find "$DESTINO" -name 'visitas-*.html' -mtime +"$INFORMES_DIAS" -print -delete | wc -l)"
[ "$BORRADOS" -gt 0 ] && echo "Retirados $BORRADOS informes de más de $INFORMES_DIAS días."

exit 0
