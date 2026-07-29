#!/usr/bin/env bash
# =============================================================================
# install.sh — Instalación del sistema de subvenciones BDNS/DGDA
#
# Uso:        bash install.sh
# Requisitos: Docker (con docker compose v2), Python 3.10+, openssl
# Plataforma: Linux · macOS · WSL2 (Windows con WSL2)
# =============================================================================

set -euo pipefail

# ── Constantes ────────────────────────────────────────────────────────────────
DOMAIN="subvencionesDGDA.local"
ENV_FILE="docker/.env"
SSL_DIR="docker/ssl"

# ── Colores ───────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    VERDE="\033[0;32m"
    AMARILLO="\033[1;33m"
    ROJO="\033[0;31m"
    NEGRITA="\033[1m"
    RESET="\033[0m"
else
    VERDE="" AMARILLO="" ROJO="" NEGRITA="" RESET=""
fi

ok()    { echo -e "${VERDE}  ✔  $*${RESET}"; }
info()  { echo -e "     $*"; }
aviso() { echo -e "${AMARILLO}  ⚠  $*${RESET}"; }
error() { echo -e "${ROJO}  ✖  $*${RESET}"; }
fase()  { echo; echo -e "${NEGRITA}$*${RESET}"; }

# ── Utilidades ────────────────────────────────────────────────────────────────

# Pide confirmación (s/N). Devuelve 0 si el usuario confirma.
confirmar() {
    local pregunta="$1"
    echo -ne "${AMARILLO}  →  ${pregunta} [s/N]: ${RESET}"
    read -r resp
    [[ "$resp" =~ ^[sS]$ ]]
}

# Espera hasta que MariaDB esté lista (180 s + 1 reintento opcional de 60 s).
esperar_db() {
    # Polling cada 2 s hasta que MariaDB acepte conexiones.
    # - Primer intento: 180 s (cubre primera instalación en WSL2 lento, donde MariaDB
    #   crea su datadir desde cero y puede tardar hasta 2-3 minutos).
    # - En reinstalaciones suele tardar 20-30 s.
    # - Si se agota, ofrece esperar 60 s más antes de abortar.
    # Se usa SELECT 1 en lugar de mysqladmin ping porque el contenedor
    # mariadb:11 no incluye mysqladmin en su imagen slim.
    local intentos=0
    local max=90
    local total=180
    echo -ne "     Esperando a la base de datos"
    while ! docker exec bdns_dgda_db mariadb \
            -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
            -e "SELECT 1" >/dev/null 2>&1; do
        intentos=$((intentos + 1))
        if [ "$intentos" -ge "$max" ]; then
            echo
            aviso "La base de datos no ha respondido en ${total} s."
            info  "En reinstalación esto suele tardar 20-30 s. En primera"
            info  "instalación con WSL2 lento puede llegar a 2-3 minutos"
            info  "porque MariaDB crea su datadir desde cero."
            if confirmar "¿Esperar 60 segundos más? Si pulsas Enter o 'n' se aborta"; then
                intentos=0
                max=30
                total=$((total + 60))
                echo -ne "     Esperando 60 s más"
            else
                echo
                error "Abortado. La base de datos seguirá arrancando en segundo plano."
                info  "Espera 1-2 minutos y vuelve a ejecutar: bash install.sh"
                info  "Si el problema persiste, comprueba los logs: docker logs bdns_dgda_db"
                exit 1
            fi
        fi
        echo -ne "."
        sleep 2
    done
    echo
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo
echo -e "${NEGRITA}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${NEGRITA}║   Subvenciones Bienestar Animal — BDNS / DGDA        ║${RESET}"
echo -e "${NEGRITA}║   Script de instalación                              ║${RESET}"
echo -e "${NEGRITA}╚══════════════════════════════════════════════════════╝${RESET}"
echo
echo "  Este script configurará el entorno completo del proyecto."
echo "  Duración estimada: 5-15 min (depende de la conexión a internet)."
echo "  Puedes interrumpirlo en cualquier momento con Ctrl+C."
echo

# ── Directorio raíz ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Limpia metadatos de zona de Windows (se generan al descomprimir ZIPs en Windows y copiar a WSL2)
find . -name "*:Zone.Identifier" -delete 2>/dev/null || true

# =============================================================================
# FASE 1 — Sistema operativo
# =============================================================================
fase "[1/7] Comprobando sistema operativo..."

OS="$(uname -s)"
case "$OS" in
    Linux*)
        if grep -qi microsoft /proc/version 2>/dev/null; then
            ok "WSL2 detectado — compatible"
        else
            ok "Linux detectado"
        fi
        ;;
    Darwin*)
        ok "macOS detectado"
        ;;
    CYGWIN*|MINGW*|MSYS*)
        error "Windows nativo no soportado. Usa WSL2 y ejecuta el script desde ahí."
        error "Guía WSL2: https://learn.microsoft.com/es-es/windows/wsl/install"
        exit 1
        ;;
    *)
        aviso "Sistema operativo no reconocido: $OS. Continuando de todas formas..."
        ;;
esac

# =============================================================================
# FASE 2 — Prerequisitos
# =============================================================================
fase "[2/7] Comprobando prerequisitos..."

FALTAN=0

# Docker
if command -v docker >/dev/null 2>&1; then
    DOCKER_VER=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    ok "Docker $DOCKER_VER"
else
    error "Docker no encontrado."
    case "$OS" in
        Linux*)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                info "WSL2: instala Docker Desktop para Windows desde https://www.docker.com/products/docker-desktop/"
                info "      Activa la integración con WSL2 en Settings → Resources → WSL Integration"
            else
                info "Linux: sudo apt install docker.io docker-compose-plugin  (Debian/Ubuntu)"
                info "       o sigue la guía oficial: https://docs.docker.com/engine/install/"
            fi
            ;;
        Darwin*)
            info "macOS: descarga Docker Desktop desde https://www.docker.com/products/docker-desktop/"
            info "       o instala OrbStack (más ligero): https://orbstack.dev"
            ;;
    esac
    FALTAN=$((FALTAN + 1))
fi

# Docker Compose v2 (subcomando de docker, no binario aparte)
if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose v2"
elif command -v docker-compose >/dev/null 2>&1; then
    aviso "Se ha encontrado docker-compose v1 (obsoleto)."
    aviso "Este proyecto requiere 'docker compose' (v2). Actualiza Docker."
    FALTAN=$((FALTAN + 1))
else
    error "docker compose no encontrado."
    FALTAN=$((FALTAN + 1))
fi

# Docker daemon en marcha
if docker info >/dev/null 2>&1; then
    ok "Docker daemon activo"
else
    error "El daemon de Docker no está en marcha."
    info "Inicia Docker Desktop o ejecuta: sudo systemctl start docker"
    FALTAN=$((FALTAN + 1))
fi

# Python 3.10+
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        ok "Python $PY_VER"
        # Comprueba venv y ensurepip por separado: en Ubuntu/Debian con Python 3.12+
        # el módulo venv existe pero ensurepip viene en un paquete aparte (python3.X-venv).
        # python3 -m venv --help pasa aunque ensurepip no esté; hay que importarlo explícitamente.
        if ! python3 -m venv --help >/dev/null 2>&1; then
            error "El módulo venv de Python no está disponible."
            info "Instálalo con: sudo apt install python${PY_VER}-venv"
            FALTAN=$((FALTAN + 1))
        elif ! python3 -c "import ensurepip" >/dev/null 2>&1; then
            error "El módulo ensurepip no está disponible — necesario para crear entornos virtuales."
            info "En Ubuntu/Debian ejecuta:"
            echo -e "${AMARILLO}    sudo apt install python${PY_VER}-venv${RESET}"
            FALTAN=$((FALTAN + 1))
        fi
    else
        error "Python $PY_VER encontrado, se necesita 3.10 o superior."
        FALTAN=$((FALTAN + 1))
    fi
else
    error "Python 3 no encontrado."
    FALTAN=$((FALTAN + 1))
fi

# openssl
if command -v openssl >/dev/null 2>&1; then
    ok "openssl $(openssl version | awk '{print $2}')"
else
    error "openssl no encontrado."
    info "Instálalo con: sudo apt install openssl  (Linux)"
    info "               brew install openssl       (macOS)"
    FALTAN=$((FALTAN + 1))
fi

if [ "$FALTAN" -gt 0 ]; then
    echo
    error "$FALTAN prerequisito(s) no cumplido(s). Instálalos y vuelve a ejecutar el script."
    error "No se ha modificado nada en tu sistema."
    exit 1
fi

# =============================================================================
# RESUMEN PREVIO — qué va a hacer el script
# =============================================================================
echo
echo -e "${NEGRITA}  El script realizará las siguientes acciones:${RESET}"
[ ! -f "docker/.env" ]           && echo "  • Crear docker/.env con credenciales de desarrollo"
[ ! -f "docker/ssl/server.crt" ] && echo "  • Generar certificado SSL autofirmado"
! grep -q "$DOMAIN" /etc/hosts 2>/dev/null && \
    echo "  • (Opcional) Añadir $DOMAIN a /etc/hosts — requiere sudo"
echo "  • Aplicar migraciones de esquema (idempotente)"
echo "  • Reconstruir y levantar los contenedores Docker"
echo "  • Cargar el dataset si la BD está vacía"
[ ! -d "venv" ] && echo "  • (Opcional) Crear entorno virtual Python"
echo
if ! confirmar "¿Continuar?"; then
    echo
    info "Instalación cancelada. No se ha modificado nada."
    exit 0
fi

# =============================================================================
# FASE 3 — Archivo .env
# =============================================================================
fase "[3/7] Configurando variables de entorno..."

if [ -f "$ENV_FILE" ]; then
    ok ".env ya existe — se usará el existente"
    aviso "Si quieres regenerarlo, bórralo manualmente y vuelve a ejecutar el script."
else
    info "Creando $ENV_FILE con valores por defecto..."

    # Genera una SECRET_KEY aleatoria de 64 caracteres hex
    SECRET_KEY_GENERADA=$(openssl rand -hex 32)

    cat > "$ENV_FILE" <<EOF
MYSQL_ROOT_PASSWORD=rootpass_bdns
MYSQL_DATABASE=bdns_dgda
MYSQL_USER=bdns_user
MYSQL_PASSWORD=bdns_pass
SECRET_KEY=${SECRET_KEY_GENERADA}
CORS_ORIGINS=*
EOF

    ok ".env creado"
    aviso "Las contraseñas son genéricas para desarrollo local."
    aviso "No uses estos valores en un servidor público."
fi

# Carga las variables para usarlas en este script
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

# =============================================================================
# FASE 4 — Certificado SSL
# =============================================================================
fase "[4/7] Certificado SSL..."

CERT="$SSL_DIR/server.crt"
KEY="$SSL_DIR/server.key"

if [ -f "$CERT" ] && [ -f "$KEY" ]; then
    ok "Certificado SSL ya existe — se reutilizará"
else
    info "Generando certificado autofirmado para $DOMAIN..."
    mkdir -p "$SSL_DIR"
    # Se usa un fichero de config temporal para compatibilidad con LibreSSL (macOS)
    # y versiones antiguas de OpenSSL que no admiten -addext.
    _SSL_CONF=$(mktemp)
    cat > "$_SSL_CONF" <<SSLCONF
[req]
distinguished_name = req_dn
x509_extensions    = v3_req
prompt             = no
[req_dn]
CN = ${DOMAIN}
O  = DAW
C  = ES
[v3_req]
subjectAltName = DNS:${DOMAIN},DNS:localhost
SSLCONF
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY" \
        -out "$CERT" \
        -config "$_SSL_CONF" \
        2>/dev/null
    rm -f "$_SSL_CONF"
    ok "Certificado generado (válido 1 año)"
    aviso "El navegador mostrará un aviso de 'No seguro' — es normal con certificados autofirmados."
    aviso "Acepta la excepción en el navegador para acceder."
fi

# =============================================================================
# FASE 5 — /etc/hosts
# =============================================================================
fase "[5/7] Dominio local ($DOMAIN)..."

if grep -q "$DOMAIN" /etc/hosts 2>/dev/null; then
    ok "$DOMAIN ya está en /etc/hosts"
else
    echo
    echo "  Para acceder con HTTPS necesitas añadir esta línea a /etc/hosts:"
    echo
    echo -e "    ${NEGRITA}127.0.0.1  ${DOMAIN}${RESET}"
    echo
    echo "  Esto requiere permisos de administrador (sudo)."
    echo

    if confirmar "¿Añadir $DOMAIN a /etc/hosts? (recomendado)"; then
        echo "127.0.0.1  ${DOMAIN}" | sudo tee -a /etc/hosts > /dev/null
        ok "Añadido a /etc/hosts"
        if grep -qi microsoft /proc/version 2>/dev/null; then
            aviso "WSL2: el navegador Windows usa su propio fichero de hosts."
            aviso "      Añade también esta línea (como administrador) en Windows:"
            aviso "      C:\\Windows\\System32\\drivers\\\\etc\\hosts"
            aviso "          127.0.0.1  ${DOMAIN}"
        fi
    else
        echo
        aviso "No se ha modificado /etc/hosts — el dominio $DOMAIN no estará disponible."
        echo
        echo "  Puedes acceder igualmente por:"
        echo -e "  ${NEGRITA}→ Web:${RESET}      http://localhost"
        echo -e "  ${NEGRITA}→ API docs:${RESET} http://localhost/docs"
        echo
        echo "  Limitaciones sin el dominio local:"
        echo "    • Sin HTTPS — el navegador no mostrará el candado"
        echo "    • Cookies con flag Secure no se enviarán"
        echo "    • El correo de recuperación de contraseña usa la URL del dominio;"
        echo "      el enlace no funcionará si no está en /etc/hosts"
        echo
        echo "  Para añadirlo manualmente en cualquier momento:"
        echo "    echo '127.0.0.1 ${DOMAIN}' | sudo tee -a /etc/hosts"
        echo
    fi
fi

# =============================================================================
# FASE 6 — Docker y base de datos
# =============================================================================
fase "[6/7] Levantando contenedores y cargando datos..."

# Detecta si la BD ya tiene datos arrancándola brevemente
TIENE_DATOS=false
FILAS=0
(cd docker && docker compose up -d db 2>/dev/null) || true
esperar_db
# ── Migraciones de esquema (siempre, idempotentes) ──────────────────────────
# Se ejecutan aunque la BD ya tenga datos: las sentencias usan IF NOT EXISTS
# y ADD COLUMN IF NOT EXISTS, por lo que son seguras de repetir.
docker exec bdns_dgda_db mariadb \
    -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
    -e "
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         INT          NOT NULL AUTO_INCREMENT,
    id_usuario INT          NOT NULL,
    token      VARCHAR(64)  NOT NULL,
    expira_en  DATETIME     NOT NULL,
    revocado   TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_token (token),
    CONSTRAINT fk_rt_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reset_tokens (
    id         INT          NOT NULL AUTO_INCREMENT,
    id_usuario INT          NOT NULL,
    token      VARCHAR(64)  NOT NULL,
    expira_en  DATETIME     NOT NULL,
    usado      TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_reset_token (token),
    CONSTRAINT fk_reset_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS verificacion_tokens (
    id         INT          NOT NULL AUTO_INCREMENT,
    id_usuario INT          NOT NULL,
    token      VARCHAR(64)  NOT NULL,
    expira_en  DATETIME     NOT NULL,
    usado      TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_verif_token (token),
    CONSTRAINT fk_verif_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre           VARCHAR(100) NULL       AFTER email;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email_verificado TINYINT(1)   NOT NULL DEFAULT 1 AFTER activo;
ALTER TABLE convocatorias ADD COLUMN IF NOT EXISTS fecha_fin_plazo DATE NULL AFTER fecha_convocatoria;
UPDATE convocatorias SET fecha_convocatoria='2021-10-26' WHERE tipo_convoc='epa'  AND anio_convocatoria=2021 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2022-08-24' WHERE tipo_convoc='epa'  AND anio_convocatoria=2022 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2023-05-19' WHERE tipo_convoc='epa'  AND anio_convocatoria=2023 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2024-06-17' WHERE tipo_convoc='epa'  AND anio_convocatoria=2024 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2025-05-05' WHERE tipo_convoc='epa'  AND anio_convocatoria=2025 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2023-05-19' WHERE tipo_convoc='eell' AND anio_convocatoria=2023 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2024-05-31' WHERE tipo_convoc='eell' AND anio_convocatoria=2024 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET fecha_convocatoria='2025-03-27' WHERE tipo_convoc='eell' AND anio_convocatoria=2025 AND fecha_convocatoria IS NULL;
UPDATE convocatorias SET titulo_convoc=CONCAT('Subvenciones a entidades locales para protección animal ', anio_convocatoria)
WHERE tipo_convoc='eell' AND LENGTH(titulo_convoc) > 60;
UPDATE convocatorias SET fecha_resolucion='2022-01-14' WHERE tipo_convoc='epa'  AND anio_convocatoria=2021 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2022-12-23' WHERE tipo_convoc='epa'  AND anio_convocatoria=2022 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2023-11-20' WHERE tipo_convoc='epa'  AND anio_convocatoria=2023 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2024-11-14' WHERE tipo_convoc='epa'  AND anio_convocatoria=2024 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2025-12-30' WHERE tipo_convoc='epa'  AND anio_convocatoria=2025 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2024-01-11' WHERE tipo_convoc='eell' AND anio_convocatoria=2023 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2024-11-20' WHERE tipo_convoc='eell' AND anio_convocatoria=2024 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_resolucion='2025-12-31' WHERE tipo_convoc='eell' AND anio_convocatoria=2025 AND fecha_resolucion IS NULL;
UPDATE convocatorias SET fecha_fin_plazo='2026-06-15' WHERE tipo_convoc='epa'  AND anio_convocatoria=2026 AND fecha_fin_plazo IS NULL;
UPDATE convocatorias SET fecha_fin_plazo='2026-06-10' WHERE tipo_convoc='eell' AND anio_convocatoria=2026 AND fecha_fin_plazo IS NULL;
" 2>/dev/null && ok "Esquema al día" || aviso "Migración omitida (BD vacía, se aplicará en el primer arranque)"

FILAS=$(docker exec bdns_dgda_db mariadb \
    -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
    -sNe "SELECT COUNT(*) FROM solicitudes" 2>/dev/null || echo "0")
if [ "${FILAS:-0}" -gt 0 ]; then TIENE_DATOS=true; fi

# Función auxiliar: asegura que las convocatorias vigentes sin resolución están en BD.
# Se ejecuta siempre (primera instalación y reinstalación) para que los avisos aparezcan.
insertar_convocatorias_vigentes() {
    docker exec bdns_dgda_db mariadb \
        -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
        -e "
INSERT INTO convocatorias (titulo_convoc, tipo_convoc, anio_convocatoria, num_convoc, periodo_meses, fecha_convocatoria, fecha_fin_plazo)
SELECT 'Subvenciones a entidades de protección animal 2026','epa',2026,'904714',12,'2026-05-11','2026-06-15'
WHERE NOT EXISTS (SELECT 1 FROM convocatorias WHERE tipo_convoc='epa' AND anio_convocatoria=2026);
INSERT INTO convocatorias (titulo_convoc, tipo_convoc, anio_convocatoria, num_convoc, periodo_meses, fecha_convocatoria, fecha_fin_plazo)
SELECT 'Subvenciones a entidades locales para protección animal 2026','eell',2026,'897468',12,'2026-04-08','2026-06-10'
WHERE NOT EXISTS (SELECT 1 FROM convocatorias WHERE tipo_convoc='eell' AND anio_convocatoria=2026);
" 2>/dev/null && ok "Convocatorias vigentes al día" || aviso "No se pudieron insertar las convocatorias 2026"
}

if $TIENE_DATOS; then
    ok "Base de datos existente con $FILAS solicitudes — no se sobreescribirá"
    aviso "Para reinstalar la BD desde cero: make reset-db"
    echo
    info "Actualizando imágenes y levantando todos los contenedores..."
    info "(El backend se reconstruye para que el código esté siempre actualizado)"
    (cd docker && docker compose up --build -d)
    insertar_convocatorias_vigentes
else
    info "Primera instalación — construyendo imágenes y descargando dependencias..."
    info "(Puede tardar varios minutos la primera vez)"
    echo
    # La BD ya está arriba (la levantamos para detectar datos), solo construimos el resto
    (cd docker && docker compose up --build -d)
    echo
    # cargar_dataset necesita PyMySQL (no está en Python del sistema).
    # Si no hay venv todavía, lo creamos aquí — la fase 7 lo detectará y lo reutilizará.
    if [ ! -d "venv" ]; then
        info "Preparando entorno Python para cargar el dataset..."
        python3 -m venv venv
        venv/bin/pip install --quiet --upgrade pip
        venv/bin/pip install --quiet -r requeriments.txt
        venv/bin/pip install --quiet -r backend/requirements.txt
        ok "Entorno Python listo"
    fi
    info "Cargando dataset en la base de datos..."
    venv/bin/python3 -m scripts.data_processing.cargar_dataset
    echo
    ok "Dataset cargado correctamente"
    insertar_convocatorias_vigentes
fi

# Cuenta de administración. Va aquí y no antes porque necesita el contenedor
# del backend levantado para generar el hash con la misma función que usa la
# aplicación. El script no hace nada si ya existe una cuenta admin.
bash scripts/crear_admin.sh

# =============================================================================
# FASE 7 — Entorno de desarrollo local (venv)
# =============================================================================
fase "[7/7] Entorno de desarrollo local (venv)..."

if [ -d "venv" ]; then
    ok "venv ya existe — se usará el existente"
else
    echo
    echo "  El venv NO es necesario para usar la aplicación web — esta ya funciona."
    echo "  Solo lo necesitas si vas a ejecutar los tests ('make test') o los scripts de parseo."
    echo "  Ocupa ~175 MB (incluye pytest y dependencias del backend)."
    echo

    if confirmar "¿Crear entorno virtual Python (venv)? (solo para tests y scripts)"; then
        python3 -m venv venv
        venv/bin/pip install --quiet --upgrade pip
        venv/bin/pip install --quiet -r requeriments.txt
        venv/bin/pip install --quiet -r backend/requirements.txt
        ok "venv creado con dependencias instaladas"
    else
        aviso "Venv omitido — la aplicación web funciona igualmente."
        aviso "Para crearlo después: python3 -m venv venv && source venv/bin/activate && pip install -r requeriments.txt -r backend/requirements.txt"
    fi
fi

# =============================================================================
# RESUMEN
# =============================================================================
echo
echo -e "${VERDE}${NEGRITA}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${VERDE}${NEGRITA}║   ¡Instalación completada!                           ║${RESET}"
echo -e "${VERDE}${NEGRITA}╚══════════════════════════════════════════════════════╝${RESET}"
echo
echo "  Acceso:"
if grep -q "$DOMAIN" /etc/hosts 2>/dev/null; then
    echo -e "  ${NEGRITA}→ Web:${RESET}      https://${DOMAIN}"
    echo -e "  ${NEGRITA}→ API docs:${RESET} https://${DOMAIN}/docs"
else
    echo -e "  ${NEGRITA}→ Web:${RESET}      http://localhost  ${AMARILLO}(sin HTTPS — dominio local no configurado)${RESET}"
    echo -e "  ${NEGRITA}→ API docs:${RESET} http://localhost/docs"
    echo
    echo -e "  ${AMARILLO}Para activar HTTPS añade el dominio a /etc/hosts:${RESET}"
    echo "    echo '127.0.0.1 ${DOMAIN}' | sudo tee -a /etc/hosts"
fi
echo -e "  ${NEGRITA}→ Mailpit:${RESET}  http://localhost:8025"
echo -e "  ${NEGRITA}→ Adminer:${RESET}  http://localhost:8080"
echo
echo "  Acceso: con la cuenta de administración que acabas de crear."
echo "  No hay registro público; las demás cuentas se crean desde el panel admin."
echo
echo "  Comandos útiles:"
echo "    make start      — levantar contenedores"
echo "    make stop       — parar contenedores"
echo "    make test       — ejecutar tests"
echo "    make logs       — ver logs del backend"
echo "    make reset-db   — reinstalar BD desde cero"
echo "    make crear-admin — crear la cuenta de administración"
echo
