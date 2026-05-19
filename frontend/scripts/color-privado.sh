#!/usr/bin/env bash
# Cambia los colores del banner, fondo y hover de privado.html / exclusivo.html
# Uso interactivo: ./scripts/color-privado.sh
# Con argumentos:  ./scripts/color-privado.sh "#2D6A4F" "#FAF4EE" "#E8F4F0"
# Omitir argumento (o dejar "") para no cambiar ese color.

CSS="$(dirname "$0")/../css/styles.css"

ACTUAL_BANNER=$(grep -Po '(?<=--banner-privado: )#[0-9a-fA-F]{6}' "$CSS")
ACTUAL_FONDO=$(grep  -Po '(?<=--fondo-privado:  )#[0-9a-fA-F]{6}' "$CSS")
ACTUAL_HOVER=$(grep  -Po '(?<=--hover-privado:  )#[0-9a-fA-F]{6}' "$CSS")

echo ""
echo "Colores actuales:"
echo "  Banner (fuerte) : $ACTUAL_BANNER"
echo "  Fondo  (claro)  : $ACTUAL_FONDO"
echo "  Hover  tarjeta  : $ACTUAL_HOVER"
echo ""

if [[ -n "$1" ]]; then NUEVO_BANNER="$1"
else read -p "Nuevo color banner  [Enter = sin cambio]: " NUEVO_BANNER; fi

if [[ -n "$2" ]]; then NUEVO_FONDO="$2"
else read -p "Nuevo color fondo   [Enter = sin cambio]: " NUEVO_FONDO; fi

if [[ -n "$3" ]]; then NUEVO_HOVER="$3"
else read -p "Nuevo color hover   [Enter = sin cambio]: " NUEVO_HOVER; fi

CAMBIOS=0

if [[ -n "$NUEVO_BANNER" ]]; then
    sed -i "s/--banner-privado: $ACTUAL_BANNER/--banner-privado: $NUEVO_BANNER/" "$CSS"
    echo "  Banner  → $NUEVO_BANNER"
    CAMBIOS=$((CAMBIOS+1))
fi

if [[ -n "$NUEVO_FONDO" ]]; then
    sed -i "s/--fondo-privado:  $ACTUAL_FONDO/--fondo-privado:  $NUEVO_FONDO/" "$CSS"
    echo "  Fondo   → $NUEVO_FONDO"
    CAMBIOS=$((CAMBIOS+1))
fi

if [[ -n "$NUEVO_HOVER" ]]; then
    sed -i "s/--hover-privado:  $ACTUAL_HOVER/--hover-privado:  $NUEVO_HOVER/" "$CSS"
    echo "  Hover   → $NUEVO_HOVER"
    CAMBIOS=$((CAMBIOS+1))
fi

if [[ $CAMBIOS -eq 0 ]]; then
    echo "Sin cambios."
else
    echo ""
    echo "Listo. Recarga el navegador para ver los cambios."
fi
