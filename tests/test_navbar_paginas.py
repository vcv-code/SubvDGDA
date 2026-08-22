"""
Que el menú de navegación funcione en todas las páginas que lo muestran.

Por qué existe este test
------------------------
Seis páginas —login, recuperar y restablecer contraseña, verificar email y las
dos de error— tenían el botón de menú en el marcado pero **no cargaban
`navbar.js`**, así que el botón no hacía nada. En móvil, donde los enlaces solo
son visibles con el menú desplegado, eso deja la página **sin navegación**.

Duele más en las de error: quien llega a un 404 ya está perdido, y el menú es
justo lo que necesita para salir.

Es un fallo invisible en escritorio —ahí los enlaces se ven siempre— y por eso
sobrevivió tanto: solo se nota en una pantalla estrecha y pulsando el botón.
"""
import re
from pathlib import Path

FRONT = Path(__file__).parent.parent / "frontend"


def _paginas_con_menu():
    return [f for f in sorted(FRONT.glob("*.html"))
            if "navbar__hamburger" in f.read_text(encoding="utf-8")]


def test_toda_pagina_con_boton_de_menu_carga_su_script():
    faltan = [f.name for f in _paginas_con_menu()
              if "js/navbar.js" not in f.read_text(encoding="utf-8")]
    assert not faltan, (
        f"Estas páginas muestran el botón de menú pero no cargan navbar.js, "
        f"así que no hace nada: {faltan}"
    )


def test_toda_pagina_con_menu_tiene_los_enlaces():
    """Sin la lista, el botón abriría un menú vacío."""
    sin_enlaces = [f.name for f in _paginas_con_menu()
                   if "navbar__links" not in f.read_text(encoding="utf-8")]
    assert not sin_enlaces, f"Botón de menú sin lista de enlaces: {sin_enlaces}"


def test_el_script_va_con_defer():
    """Sin `defer` el script correría antes de existir el botón."""
    for f in _paginas_con_menu():
        linea = next(l for l in f.read_text(encoding="utf-8").split("\n")
                     if "js/navbar.js" in l)
        assert "defer" in linea, f"{f.name}: navbar.js sin defer"
