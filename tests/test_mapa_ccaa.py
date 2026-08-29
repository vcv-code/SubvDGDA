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


# ─────────────────────────────────────────────
# Mapa base
# En agosto de 2026 CARTO empezó a exigir clave y el mapa se llenó de marcas de
# agua «API KEY REQUIRED» sin que hubiera cambiado nada en el proyecto. Se
# retiró el mapa base: las comunidades salen del GeoJSON local y el fondo lo
# pone el CSS, así que ya no hay proveedor externo que pueda cambiar de reglas.
# ─────────────────────────────────────────────

def test_el_mapa_no_depende_de_teselas_externas():
    from pathlib import Path
    js = Path("frontend/js/mapa-ccaa.js").read_text(encoding="utf-8")
    assert "L.tileLayer" not in js, (
        "volver a añadir un mapa base ata la web a un tercero que puede exigir "
        "clave, y además envía la IP de cada visitante a ese servidor"
    )
    for proveedor in ("cartocdn", "carto.com", "tile.openstreetmap.org",
                      "basemaps", "mapbox"):
        assert proveedor not in js, f"referencia a un proveedor de mapas: {proveedor}"


def test_las_comunidades_salen_de_un_fichero_local():
    from pathlib import Path
    js = Path("frontend/js/mapa-ccaa.js").read_text(encoding="utf-8")
    assert "'/assets/geojson/ccaa.geojson'" in js
    assert Path("frontend/assets/geojson/ccaa.geojson").exists()


def test_el_contenedor_del_mapa_tiene_fondo_propio():
    """Sin teselas, ese color ES el mapa base: si faltara, quedaría en blanco."""
    from pathlib import Path
    css = Path("frontend/css/styles.css").read_text(encoding="utf-8")
    bloque = css[css.index("#mapa-ccaa {"):]
    bloque = bloque[:bloque.index("}")]
    assert "background-color" in bloque


# ─────────────────────────────────────────────
# Acceso al detalle en móvil
# En escritorio basta un clic para abrir el top de municipios. En móvil la única
# vía era un DOBLE TOQUE, un gesto que nadie adivina: se veía menos información
# que en escritorio y sin pista de cómo llegar al resto.
# ─────────────────────────────────────────────

def test_la_caja_de_info_movil_ofrece_un_boton_al_detalle():
    from pathlib import Path
    js = Path("frontend/js/mapa-ccaa.js").read_text(encoding="utf-8")
    assert "mapa-info-central__ver" in js
    assert "Ver top de municipios" in js


def test_el_boton_del_mapa_es_pulsable():
    """La caja lleva `pointer-events: none` para que los toques lleguen al mapa.

    El botón heredaría ese `none` y no respondería a nada: necesita `auto`
    explícito. La primera versión de este botón tenía justo ese fallo.
    """
    from pathlib import Path
    css = Path("frontend/css/styles.css").read_text(encoding="utf-8")
    bloque = css[css.index(".mapa-info-central__ver {"):]
    bloque = bloque[:bloque.index("}")]
    assert "pointer-events" in bloque and "auto" in bloque


def test_el_doble_toque_sigue_valiendo_como_atajo():
    """Se mantiene, pero con un umbral más tolerante: 400 ms era exigente para
    quien no sabe que tiene que tocar rápido."""
    import re
    from pathlib import Path
    js = Path("frontend/js/mapa-ccaa.js").read_text(encoding="utf-8")
    ms = int(re.search(r"DOBLE_TOQUE_MS = (\d+)", js).group(1))
    assert ms >= 500, f"umbral de doble toque demasiado corto: {ms} ms"
