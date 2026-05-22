#!/usr/bin/env bash
# uninstall.sh — Elimina el entorno de desarrollo de Subvenciones BDNS/DGDA
#
# Revierte lo que hizo install.sh:
#   1. Para y elimina los contenedores Docker (con sus volúmenes y datos)
#   2. Elimina la imagen Docker del backend
#   3. Elimina la entrada de /etc/hosts  (requiere sudo)
#   4. Elimina los archivos generados: docker/.env, docker/ssl/, venv/
#
# Uso:
#   bash uninstall.sh
#
# ADVERTENCIA: los datos de la base de datos se perderán al eliminar los volúmenes.

DOMAIN="subvencionesDGDA.local"
DOCKER_DIR="docker"

# Comprobar que se ejecuta desde la raíz del proyecto
if [ ! -f "${DOCKER_DIR}/docker-compose.yml" ]; then
    echo "  Error: ejecuta el script desde la raíz del proyecto."
    echo "  Ejemplo: cd /ruta/al/proyecto && bash uninstall.sh"
    exit 1
fi

# ── Colores ──────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    VERDE="\033[0;32m" AMARILLO="\033[0;33m" ROJO="\033[0;31m"
    NEGRITA="\033[1m"  RESET="\033[0m"
else
    VERDE="" AMARILLO="" ROJO="" NEGRITA="" RESET=""
fi

ok()        { echo -e "${VERDE}  ✔  $*${RESET}"; }
aviso()     { echo -e "${AMARILLO}  ⚠  $*${RESET}"; }
error()     { echo -e "${ROJO}  ✖  $*${RESET}"; exit 1; }
confirmar() {
    local pregunta="$1"
    echo -ne "${AMARILLO}  →  ${pregunta} [s/N]: ${RESET}"
    read -r respuesta
    [[ "$respuesta" =~ ^[sS]$ ]]
}

# ── Cabecera ─────────────────────────────────────────────────────────────────
echo
echo -e "${NEGRITA}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${NEGRITA}║   Subvenciones Bienestar Animal — BDNS / DGDA        ║${RESET}"
echo -e "${NEGRITA}║   Script de desinstalación                           ║${RESET}"
echo -e "${NEGRITA}╚══════════════════════════════════════════════════════╝${RESET}"
echo
echo -e "${ROJO}  ADVERTENCIA: esta operación es irreversible.${RESET}"
echo    "  Se eliminarán los contenedores, volúmenes (BD y datos) y archivos generados."
echo

if ! confirmar "¿Segura de que quieres desinstalar?"; then
    echo
    echo "  Desinstalación cancelada."
    exit 0
fi

# ── 1. Contenedores y volúmenes Docker ───────────────────────────────────────
echo
echo -e "${NEGRITA}[1/4] Deteniendo y eliminando contenedores y volúmenes...${RESET}"

if [ -f "${DOCKER_DIR}/docker-compose.yml" ]; then
    (cd "${DOCKER_DIR}" && docker compose down -v --remove-orphans 2>/dev/null) \
        && ok "Contenedores y volúmenes eliminados" \
        || aviso "No había contenedores en ejecución o ya estaban parados"
else
    aviso "No se encontró docker-compose.yml — se omite este paso"
fi

# ── 2. Imagen Docker del backend (opcional) ───────────────────────────────────
echo
echo -e "${NEGRITA}[2/4] Imagen Docker del backend...${RESET}"

if docker image inspect docker-backend >/dev/null 2>&1; then
    echo "  La imagen Docker es una copia compilada del servidor backend."
    echo "  Si no vas a volver a usar este proyecto, puedes eliminarla (libera ~200 MB)."
    echo "  Si la conservas, una futura reinstalación será más rápida."
    if confirmar "¿Eliminar la imagen Docker del backend?"; then
        docker rmi docker-backend 2>/dev/null && ok "Imagen eliminada" \
            || aviso "No se pudo eliminar la imagen"
    else
        aviso "Imagen conservada"
    fi
else
    ok "La imagen docker-backend no existe — nada que eliminar"
fi

# ── 3. Entrada en /etc/hosts ──────────────────────────────────────────────────
echo
echo -e "${NEGRITA}[3/4] Entrada en /etc/hosts...${RESET}"

if grep -q "${DOMAIN}" /etc/hosts 2>/dev/null; then
    echo "  El archivo /etc/hosts asocia el nombre '${DOMAIN}' con tu ordenador."
    echo "  Si lo eliminas, ese nombre dejará de funcionar (solo afecta a este proyecto)."
    if confirmar "¿Eliminar '${DOMAIN}' de /etc/hosts? (requiere contraseña de administrador)"; then
        sudo sed -i "/${DOMAIN}/d" /etc/hosts \
            && ok "Eliminado de /etc/hosts" \
            || aviso "No se pudo modificar /etc/hosts"

        # Aviso WSL2 para el hosts de Windows
        if grep -qi microsoft /proc/version 2>/dev/null; then
            aviso "WSL2: recuerda eliminar también la línea de:"
            aviso "      C:\\Windows\\System32\\drivers\\etc\\hosts"
        fi
    else
        aviso "Entrada en /etc/hosts conservada"
    fi
else
    ok "${DOMAIN} no está en /etc/hosts — nada que eliminar"
fi

# ── 4. Archivos generados ─────────────────────────────────────────────────────
echo
echo -e "${NEGRITA}[4/4] Archivos generados por install.sh...${RESET}"

# .env
if [ -f "${DOCKER_DIR}/.env" ]; then
    echo "  docker/.env contiene las contraseñas generadas al instalar (base de datos, clave JWT)."
    echo "  Si reinstalas, el script las genera de nuevo automáticamente."
    if confirmar "¿Eliminar docker/.env?"; then
        rm "${DOCKER_DIR}/.env" && ok "docker/.env eliminado"
    else
        aviso "docker/.env conservado"
    fi
else
    ok "docker/.env no existe — nada que eliminar"
fi

# Certificado SSL
if [ -d "${DOCKER_DIR}/ssl" ]; then
    rm -rf "${DOCKER_DIR}/ssl" && ok "docker/ssl/ eliminado"
else
    ok "docker/ssl/ no existe — nada que eliminar"
fi

# Entorno virtual Python
if [ -d "venv" ]; then
    echo "  venv/ es el entorno Python que usa el script de carga de datos (~50 MB)."
    echo "  Si reinstalas, se crea de nuevo en unos segundos."
    if confirmar "¿Eliminar venv/?"; then
        rm -rf venv && ok "venv/ eliminado"
    else
        aviso "venv/ conservado"
    fi
else
    ok "venv/ no existe — nada que eliminar"
fi

# ── Fin ───────────────────────────────────────────────────────────────────────
echo
echo -e "${VERDE}${NEGRITA}  Desinstalación completada.${RESET}"
echo
echo "  Si quieres eliminar también el código fuente, borra la carpeta del proyecto:"
echo -e "    ${NEGRITA}cd .. && rm -rf $(basename "$PWD")${RESET}"
echo
echo "  Para reinstalar desde cero: bash install.sh"
echo
