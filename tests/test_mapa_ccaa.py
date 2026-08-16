"""
Mapa de calor por CCAA (frontend/js/mapa-ccaa.js).

Comprobaciones de fichero, no necesitan navegador ni Docker.
"""
from pathlib import Path

MAPA = Path(__file__).parent.parent / "frontend/js/mapa-ccaa.js"


def test_el_tooltip_del_mapa_no_se_enlaza_en_tactil():
    """Enlazar y deshacer deja escuchadores huérfanos que revientan.

    `bindTooltip()` añade escuchadores de foco sobre el <path> del SVG, y
    `unbindTooltip()` pone `_tooltip` a null SIN retirarlos. Al recibir foco
    una comunidad, el escuchador huérfano hace `this._tooltip._source = ...`
    sobre null: "Cannot set properties of null". Se veía en la consola al
    tocar el mapa en móvil.

    La solución es no enlazarlo en táctil, no deshacerlo después.
    """
    js = MAPA.read_text(encoding="utf-8")
    assert "unbindTooltip" not in js.replace("`unbindTooltip()`", ""), (
        "unbindTooltip() ha vuelto: enlazar y deshacer deja escuchadores de "
        "foco huérfanos sobre el SVG. No enlazar el tooltip en táctil."
    )
    i = js.index("bindTooltip(html")
    contexto = js[max(0, i - 400):i]
    assert "if (!esTactilPrimario)" in contexto, (
        "bindTooltip debe quedar dentro de `if (!esTactilPrimario)`"
    )
