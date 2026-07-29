#!/usr/bin/env bash
# =============================================================================
# crear_admin.sh — Crea la cuenta de administración de la aplicación
# =============================================================================
# Es la ÚNICA vía de alta de la primera cuenta. Ni `modelo-fisico.sql` ni
# `install.sh` siembran usuarios con contraseña escrita: mientras un hash
# válido viviera en el repositorio, cualquiera que lo leyese conocería la
# contraseña de administración de todo despliegue nuevo. Aquí se pide al
# instalar, así que la credencial del sitio real no existe en el código.
#
# Lo usan install.sh, `make crear-admin` y `make reset-db` (que si no, tras
# recrear la base de datos te dejaría sin ninguna cuenta con la que entrar).
#
# Uso:
#   scripts/crear_admin.sh                 → pregunta email y contraseña
#   ADMIN_EMAIL=... ADMIN_PASSWORD=... scripts/crear_admin.sh
#                                          → sin preguntar (CI, automatización)
#
# El hash bcrypt lo genera el contenedor del backend, que ya trae la misma
# función que usa la aplicación (`hashear_password`). Así el hash se produce
# exactamente igual que en un cambio de contraseña desde la web, y no hace
# falta que el host tenga Python con bcrypt instalado.
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="docker/.env"

if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    set -a; . "$ENV_FILE"; set +a
fi
MYSQL_USER="${MYSQL_USER:-bdns_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-bdns_pass}"
MYSQL_DATABASE="${MYSQL_DATABASE:-bdns_dgda}"

if [ -t 1 ]; then
    VERDE="\033[0;32m"; ROJO="\033[0;31m"; AMARILLO="\033[1;33m"; RESET="\033[0m"
else
    VERDE=""; ROJO=""; AMARILLO=""; RESET=""
fi
ok()     { echo -e "  ${VERDE}✓${RESET} $1"; }
error()  { echo -e "  ${ROJO}✗${RESET} $1"; }
aviso()  { echo -e "  ${AMARILLO}!${RESET} $1"; }

# ── Comprobaciones previas ───────────────────────────────────────────────────

for c in bdns_dgda_db bdns_api; do
    if ! docker ps --format '{{.Names}}' | grep -qx "$c"; then
        error "El contenedor $c no está levantado."
        echo "     Arranca el entorno con 'make start' y vuelve a intentarlo."
        exit 1
    fi
done

sql() {
    docker exec -i bdns_dgda_db mariadb \
        -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" "$@"
}

# Si ya hay administración, no se toca nada: este script crea, no reemplaza.
# Para cambiar una contraseña existente está el flujo de recuperación de la
# propia web, que no obliga a tener acceso al servidor.
EXISTENTES=$(sql -sNe "SELECT COUNT(*) FROM usuarios WHERE rol='admin'" 2>/dev/null || echo "0")
if [ "${EXISTENTES:-0}" -gt 0 ]; then
    ok "Ya existe una cuenta de administración — no se crea ninguna"
    exit 0
fi

# ── Datos de la cuenta ───────────────────────────────────────────────────────

EMAIL="${ADMIN_EMAIL:-}"
PASSWORD="${ADMIN_PASSWORD:-}"

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ]; then
    if [ ! -t 0 ]; then
        error "No hay cuenta de administración y no se puede preguntar (entrada no interactiva)."
        echo "     Define ADMIN_EMAIL y ADMIN_PASSWORD, o ejecuta 'make crear-admin' en una terminal."
        exit 1
    fi
    echo
    echo "  Vamos a crear la cuenta de administración."
    echo "  Es la única forma de entrar: no hay registro público y la contraseña"
    echo "  no viene puesta en el código."
    echo
fi

while [ -z "$EMAIL" ]; do
    read -r -p "  Email de administración: " EMAIL
    case "$EMAIL" in
        *@*.*) ;;
        *) error "Eso no parece un email."; EMAIL="" ;;
    esac
done

# Mismas reglas que valida el backend (validar_password_segura en schemas.py).
# Si divergen, aquí pasaría una contraseña que la web rechazaría al cambiarla.
password_valida() {
    local p="$1"
    [ ${#p} -ge 8 ]           || { error "Mínimo 8 caracteres.";        return 1; }
    [[ "$p" == *[A-Z]* ]]     || { error "Falta una mayúscula.";        return 1; }
    [[ "$p" == *[a-z]* ]]     || { error "Falta una minúscula.";        return 1; }
    [[ "$p" == *[0-9]* ]]     || { error "Falta un número.";            return 1; }
    return 0
}

if [ -n "$PASSWORD" ]; then
    password_valida "$PASSWORD" || exit 1
else
    while true; do
        read -r -s -p "  Contraseña (8+, con mayúscula, minúscula y número): " PASSWORD; echo
        password_valida "$PASSWORD" || continue
        read -r -s -p "  Repite la contraseña: " PASSWORD2; echo
        [ "$PASSWORD" = "$PASSWORD2" ] && break
        error "No coinciden."
    done
fi

# ── Alta ─────────────────────────────────────────────────────────────────────

# La contraseña viaja por stdin, no por argv: los argumentos de un proceso son
# visibles para cualquiera que liste procesos mientras se ejecuta.
HASH=$(printf '%s' "$PASSWORD" | docker exec -i bdns_api python -c \
    "import sys; from app.auth import hashear_password; print(hashear_password(sys.stdin.read()))")

if [ -z "$HASH" ]; then
    error "No se pudo generar el hash de la contraseña."
    exit 1
fi

# email_verificado=1 porque la crea quien administra el servidor, no hay
# dirección que confirmar: sin esto el login devolvería 403 y nadie podría
# entrar a verificar a nadie.
sql <<SQL
INSERT INTO usuarios (email, nombre, password, rol, activo, email_verificado, created_at)
VALUES ('${EMAIL}', 'Administración', '${HASH}', 'admin', 1, 1, NOW());
SQL

ok "Cuenta de administración creada: ${EMAIL}"
aviso "Guarda la contraseña: no se puede recuperar desde aquí, solo restablecer por email."
