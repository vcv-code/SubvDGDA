"""
El índice de secciones de styles.css debe reflejar el cuerpo del archivo.

Por qué existe este test
------------------------
El índice de la cabecera se quedó atrás respecto al cuerpo: llegó a listar 28
secciones cuando había 35, con la numeración descolocada (decía que la 21 era
«Estadísticas» y en el cuerpo era «Botones adicionales»). Un índice que miente
es peor que no tener índice, porque se consulta justo cuando hace falta:
al buscar dónde tocar algo en 5.600 líneas.

Es una desincronización silenciosa —nada falla, solo despista— así que la
única forma de que no vuelva a pasar es comprobarla automáticamente.

Sobre la numeración
-------------------
Los números NO son correlativos y cuatro están repetidos. Es deliberado: la
documentación cita las secciones por número (47 referencias), y una de ellas
es un historial, que no debe reescribirse. Renumerar aquí dejaría esas citas
apuntando a secciones equivocadas. El cuerpo manda; el índice lo refleja.
"""
import re
from pathlib import Path

CSS = Path(__file__).parent.parent / "frontend/css/styles.css"

# Dos estilos de cabecera conviven en el archivo, ambos válidos:
#   "   12. GRIDS"                    y   "SECCIÓN 36 — MODAL DE ENTIDAD"
_FORMATO_A = re.compile(r"   (\d+)\.\s+(\S.*?)\s*$")
_FORMATO_B = re.compile(r"\s*SECCI[ÓO]N (\d+)\s*[—-]\s*(\S.*?)\s*$")


def _partir():
    """Separa la cabecera (índice) del cuerpo del archivo."""
    lineas = CSS.read_text(encoding="utf-8").split("\n")
    ini = next(i for i, l in enumerate(lineas) if "ÍNDICE DE SECCIONES" in l)
    fin = next(i for i, l in enumerate(lineas[ini:], ini)
               if l.strip().startswith("===") and i > ini)
    return lineas[ini:fin], lineas[fin:]


def _secciones_del_cuerpo():
    _, cuerpo = _partir()
    out = []
    for l in cuerpo:
        m = _FORMATO_A.match(l) or _FORMATO_B.match(l)
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def _secciones_del_indice():
    cabecera, _ = _partir()
    # Entradas del índice: "    7)  12.  GRIDS"
    ent = re.compile(r"\s*\d+\)\s*(\d+)\.\s+(.*?)(?:\s*⚠.*)?\s*$")
    return [(int(m.group(1)), m.group(2))
            for l in cabecera if (m := ent.match(l))]


def test_el_indice_lista_todas_las_secciones_del_cuerpo():
    """Si se añade una sección y no se anota en el índice, esto falla."""
    cuerpo, indice = _secciones_del_cuerpo(), _secciones_del_indice()
    assert len(indice) == len(cuerpo), (
        f"El índice lista {len(indice)} secciones y el cuerpo tiene "
        f"{len(cuerpo)}. Actualiza la cabecera de styles.css."
    )


def test_el_indice_respeta_el_orden_y_los_numeros_del_cuerpo():
    """El índice va en orden de aparición, con el número real de cada sección."""
    cuerpo, indice = _secciones_del_cuerpo(), _secciones_del_indice()
    for pos, (esperado, real) in enumerate(zip(cuerpo, indice), 1):
        assert esperado[0] == real[0], (
            f"Entrada {pos} del índice: dice sección {real[0]} y en el cuerpo "
            f"es la {esperado[0]} ({esperado[1]})"
        )
        assert esperado[1].lower() == real[1].lower(), (
            f"Sección {esperado[0]}: el índice la titula «{real[1]}» y el "
            f"cuerpo «{esperado[1]}»"
        )


def test_los_numeros_repetidos_estan_marcados():
    """Cuatro números aparecen dos veces (11, 25, 29, 30).

    No se renumeran porque la documentación los cita, pero quien lea el
    índice tiene que verlo: citar «sección 29» a secas es ambiguo.
    """
    cabecera, _ = _partir()
    nums = [n for n, _ in _secciones_del_cuerpo()]
    repes = {n for n in nums if nums.count(n) > 1}
    # Solo entradas del índice: la nota explicativa también menciona
    # «(11, 25, 29 y 30)» y llevaría a contarla como una entrada más.
    entrada = re.compile(r"\s*\d+\)\s*\d+\.\s")
    marcadas = sum(1 for l in cabecera if "⚠" in l and entrada.match(l))
    assert marcadas == sum(nums.count(n) for n in repes), (
        f"Números repetidos {sorted(repes)}: hay {marcadas} entradas marcadas "
        f"con ⚠ y deberían ser {sum(nums.count(n) for n in repes)}"
    )


def test_el_indice_explica_por_que_no_se_renumera():
    """Sin la explicación, alguien «arreglará» la numeración y romperá las citas."""
    cabecera = "\n".join(_partir()[0])
    assert "Renumerar" in cabecera and "47" in cabecera, (
        "Falta en el índice la nota que explica por qué no se renumera. "
        "Sin ella, el siguiente que pase lo verá como un descuido."
    )

