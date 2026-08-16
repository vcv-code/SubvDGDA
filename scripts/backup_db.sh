#!/usr/bin/env bash
# =============================================================================
# backup_db.sh — Volcado de la base de datos, con rotación
# =============================================================================
# Sirve igual en local (`make backup`) y en el servidor (tarea programada).
#
# Las credenciales salen de docker/.env, nunca escritas aquí: en un despliegue
# real son aleatorias y este fichero está versionado.
#
# NO se ejecuta desde el contenedor de cron del proyecto: para volcar la base de
# datos haría falta darle acceso al demonio de Docker, y eso es un permiso que
# no debe tener. En el servidor va como tarea programada del propio sistema.
#
# Uso:
#   scripts/backup_db.sh                  → volcado + rotación
#   BACKUP_DIAS=7 scripts/backup_db.sh    → conservar solo 7 días
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="docker/.env"
CONTENEDOR="bdns_dgda_db"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: falta $ENV_FILE — ejecuta 'bash install.sh'." >&2
    exit 1
fi
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

# La configuración se lee DESPUÉS de cargar el .env, y no es un detalle: así la
# retención se define UNA VEZ por entorno, en docker/.env, y vale igual para la
# tarea programada y para un `make backup` lanzado a mano.
#
# Leyéndola antes, habría que pasarla en la línea del cron, y un `make backup`
# manual usaría el valor por defecto — borrando copias que se querían conservar.
#
# Frecuencia y retención van unidas: con copias semanales, 30 días dejan solo
# cuatro. En el servidor conviene BACKUP_DIAS=180 (unas 26 copias, ~21 MB).
DIR="${BACKUP_DIR:-backups}"
DIAS="${BACKUP_DIAS:-30}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTENEDOR"; then
    echo "ERROR: el contenedor $CONTENEDOR no está levantado." >&2
    exit 1
fi

mkdir -p "$DIR"
FICHERO="$DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

# El fichero se borra si algo falla: la redirección lo crea ANTES de que
# mariadb-dump escriba nada, así que un fallo dejaría un .sql de 0 bytes con
# pinta de backup bueno — justo lo que no quieres encontrarte al restaurar.
if ! docker exec "$CONTENEDOR" mariadb-dump \
        -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$FICHERO" 2>/dev/null; then
    rm -f "$FICHERO"
    echo "ERROR: no se pudo volcar la base de datos." >&2
    exit 1
fi

# Comprobación de integridad. Que el comando termine bien no basta: un corte a
# mitad (disco lleno, contenedor parado en marcha) puede dejar un fichero
# truncado que parece válido. mariadb-dump escribe esta línea al final, así que
# si está, el volcado llegó hasta el final.
if ! tail -5 "$FICHERO" | grep -q "Dump completed"; then
    rm -f "$FICHERO"
    echo "ERROR: el volcado quedó incompleto (sin marca de cierre). Descartado." >&2
    exit 1
fi

echo "Backup guardado: $FICHERO ($(du -h "$FICHERO" | cut -f1))"

# Rotación: sin ella, un volcado diario llena el disco con el tiempo.
BORRADOS=$(find "$DIR" -maxdepth 1 -name 'backup_*.sql' -type f -mtime "+$DIAS" -print -delete | wc -l)
if [ "$BORRADOS" -gt 0 ]; then
    echo "Rotación: $BORRADOS backup(s) de más de $DIAS días eliminados"
fi

echo "Conservados: $(find "$DIR" -maxdepth 1 -name 'backup_*.sql' -type f | wc -l) volcado(s)"
