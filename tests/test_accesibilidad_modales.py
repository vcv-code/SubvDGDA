"""
El foco tiene que salir de un modal ANTES de marcarlo `aria-hidden`.

Si un descendiente conserva el foco, el navegador rechaza el atributo entero
—lo avisa por consola— y el modal sigue expuesto a los lectores de pantalla
pese a estar cerrado a la vista. Se detectó en `modal-entidad` y estaba igual
en otros dos.
"""
import re
from pathlib import Path

import pytest

# (fichero, variable del elemento) de los modales que usan aria-hidden.
# `modal-ccaa.js` se oculta con display:none, que sí saca el foco solo.
MODALES = [
    ("frontend/js/modal-entidad.js",  "backdrop"),
    ("frontend/js/modal-grafica.js",  "modal"),
    ("frontend/js/exclusiones.js",    "modalCausas"),
]


@pytest.mark.parametrize("ruta,elemento", MODALES)
def test_el_foco_sale_antes_del_aria_hidden(ruta, elemento):
    fuente = Path(ruta).read_text(encoding="utf-8")
    # `rindex`, no `index`: algunos modales se crean ya ocultos (aria-hidden al
    # construir el elemento), y ese uso es correcto porque todavía no existe ni
    # puede tener el foco dentro. El que importa es el del cierre, que es el
    # último del fichero.
    ocultar = fuente.rindex(f"{elemento}.setAttribute('aria-hidden', 'true')")
    # El respaldo por `blur` tiene que estar antes de esa línea, no después.
    respaldo = fuente.index(f"{elemento}.contains(document.activeElement)")
    assert respaldo < ocultar, (
        f"{ruta}: se marca aria-hidden antes de sacar el foco; el navegador "
        f"rechazará el atributo si el botón de cerrar aún lo tiene"
    )


@pytest.mark.parametrize("ruta,elemento", MODALES)
def test_la_comprobacion_del_foco_no_es_una_alternativa(ruta, elemento):
    """El `blur` de respaldo NO puede colgar de un `else`.

    Primer intento de arreglo: `if (opener) opener.focus(); else if (…) blur();`.
    No servía. La ficha del buscador se abre desde una `<tr>`, y `focus()` sobre
    una fila de tabla no hace nada y tampoco lanza error: el opener existía, se
    entraba por la primera rama, el foco no se movía y el `else` nunca corría.
    La comprobación tiene que ejecutarse siempre.
    """
    fuente = Path(ruta).read_text(encoding="utf-8")
    assert "document.activeElement.blur()" in fuente
    contiene = f"{elemento}.contains(document.activeElement)"
    linea = next(l for l in fuente.splitlines() if contiene in l)
    assert not linea.lstrip().startswith("} else"), (
        f"{ruta}: la comprobación del foco cuelga de un `else`, así que no corre "
        f"cuando el opener existe pero no es enfocable"
    )


def test_el_contador_de_resultados_se_puede_apilar_en_movil():
    """Iba todo en una línea y el navegador la partía por cualquier punto."""
    css = Path("frontend/css/styles.css").read_text(encoding="utf-8")
    assert ".info-resultados__rango::before" in css
    for js in ("frontend/js/solicitudes.js", "frontend/js/exclusiones.js"):
        fuente = Path(js).read_text(encoding="utf-8")
        assert "info-resultados__total" in fuente
        assert "info-resultados__rango" in fuente
        # El separador vive en el CSS, no en el texto: si volviera al texto,
        # en móvil se quedaría colgando al final de la primera línea.
        assert "resultados · Mostrando" not in fuente
        assert "exclusiones · Mostrando" not in fuente
