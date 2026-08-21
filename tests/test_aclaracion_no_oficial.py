"""
La web tiene que dejar claro que no es oficial.

Por qué existe este test
------------------------
El sitio se llama «Subvenciones DGDA», el dominio es `subvencionesdgda.org` y
el contenido son subvenciones públicas. Todo suena a organismo oficial, y hay
un riesgo real de que alguien crea que aquí se tramitan ayudas y escriba
pidiendo el estado de su expediente —o peor, que dé por hecho que lo que lee
tiene carácter oficial—.

La aclaración va en el PIE, no solo en el inicio, porque quien llega desde un
buscador aterriza en cualquier página: en el buscador de solicitudes o en una
de estadísticas, nunca necesariamente en la portada.
"""
from pathlib import Path

FRONT = Path(__file__).parent.parent / "frontend"

# mantenimiento.html no tiene pie: es una página mínima que se sirve cuando
# todo lo demás está apagado.
SIN_PIE = {"mantenimiento.html"}


def _con_pie():
    return [f for f in sorted(FRONT.glob("*.html")) if f.name not in SIN_PIE]


def test_todas_las_paginas_con_pie_aclaran_que_no_es_oficial():
    faltan = [f.name for f in _con_pie()
              if "footer-principal__aclaracion" not in f.read_text(encoding="utf-8")]
    assert not faltan, (
        f"Sin la aclaración en el pie: {faltan}. Quien llega desde un buscador "
        "puede aterrizar en cualquier página, no solo en el inicio."
    )


def test_la_aclaracion_niega_las_dos_confusiones_posibles():
    """Que no es oficial, y que no tramita nada.

    Las fuentes NO se repiten aquí: la línea de debajo del pie ya las nombra
    con sus enlaces completos, y decirlo dos veces alargaba la aclaración sin
    aportar.
    """
    t = (FRONT / "buscador.html").read_text(encoding="utf-8")
    i = t.index("footer-principal__aclaracion")
    bloque = t[i:i + 400].lower()
    assert "independiente" in bloque and "no oficial" in bloque
    assert "no gestiona ni tramita" in bloque


def test_las_fuentes_siguen_nombradas_en_el_pie_con_sus_enlaces():
    """Al quitarlas de la aclaración, tienen que seguir estando debajo."""
    t = (FRONT / "buscador.html").read_text(encoding="utf-8")
    assert "Datos procedentes de la" in t
    assert "Base de Datos Nacional de Subvenciones" in t


def test_el_inicio_lo_dice_tambien_en_el_texto_principal():
    """En la portada, donde se explica el proyecto, y no solo al final."""
    t = (FRONT / "index.html").read_text(encoding="utf-8")
    i = t.index("portada-split__descripcion")
    assert "independiente y no oficial" in t[i:i + 600]
