"""
Bloque «Qué ha pasado después: la justificación de las ayudas».

Estos datos NO salen de la BDNS ni de la API: proceden de una respuesta de
transparencia de la Secretaría de Estado de Derechos Sociales (9-9-2026). Por
eso van escritos en el HTML, que es la excepción, y por eso se vigilan aquí:
cuando llegue información nueva hay que tocar la página a mano y es fácil
dejarse algo a medias —la fecha vieja, un recuento que ya no cuadra—.

LO MÁS IMPORTANTE que comprueba este fichero es que la página NO diga que
alguien devolvió dinero. La respuesta dice literalmente que no hay renuncias,
ni pérdidas del derecho al cobro, ni expedientes de reintegro: lo único que
consta son justificaciones presentadas fuera de plazo. Son cosas distintas, y
confundirlas sería afirmar algo falso sobre ayuntamientos a los que se nombra.
"""
import re
from pathlib import Path

HTML = Path("frontend/estadisticas-eell.html").read_text(encoding="utf-8")
CSS = Path("frontend/css/styles.css").read_text(encoding="utf-8")


def _bloque():
    ini = HTML.index('<!-- /fila 5 exclusiones -->')
    return HTML[ini:HTML.index('<!-- /fila 6 justificación -->')]


def _texto_plano():
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _bloque()))


def test_el_bloque_existe():
    assert "la justificación de las ayudas" in HTML
    assert '<!-- /fila 6 justificación -->' in HTML


def test_no_se_afirma_que_nadie_devolviera_dinero():
    """El error que este bloque NO puede cometer.

    La respuesta administrativa distingue cuatro supuestos y solo uno tiene
    nombres detrás. Decir que estos ayuntamientos «devolvieron» o «perdieron»
    la subvención sería falso: lo que consta es que no justificaron en plazo.
    """
    texto = _texto_plano()
    assert "no hay dinero devuelto ni recuperado" in texto
    assert "no presentaron la justificación en plazo" in texto
    for prohibido in ("han devuelto la subvención", "perdieron la ayuda",
                      "se les ha retirado"):
        assert prohibido not in texto, f"afirmación no sostenida: {prohibido}"


def test_estan_los_tres_hallazgos_negativos():
    """Son el titular: que no se haya recuperado nada es el dato."""
    texto = _texto_plano()
    assert "Ninguna entidad local ha renunciado" in texto
    assert "Ninguna ha perdido el derecho al cobro" in texto
    assert "No consta ningún expediente de reintegro" in texto


def test_el_recuento_coincide_con_las_listas():
    """Si se añade o quita una entidad, el titular del desplegable miente."""
    bloque = _bloque()
    det = bloque.split('<details')
    assert len(det) == 3, "deberían ser dos desplegables, 2023 y 2024"

    n23 = det[1].count("<li>")
    n24 = det[2].count("<li>")
    assert n23 == 5, f"2023: {n23} entidades, el texto dice 5"
    assert n24 == 21, f"2024: {n24} entidades, el texto dice 21"
    assert "5 entidades fuera de plazo" in det[1]
    assert "21 entidades fuera de plazo" in det[2]


def test_los_expedientes_estan_bien_formados_y_no_se_repiten():
    """Un número de expediente mal copiado señala a quien no es.

    Ojo: 2023 y 2024 NO usan el mismo formato en el original —2023 va sin
    barra y 2024 con ella—, así que se respeta tal cual viene.
    """
    exps = re.findall(r'class="justif__exp">([^<]+)</span>', _bloque())
    assert len(exps) == 26, f"{len(exps)} expedientes, deberían ser 26"
    assert len(set(exps)) == len(exps), "hay expedientes repetidos"
    for e in exps:
        assert re.fullmatch(r"EXP2023\d{6}|EXP2024/\d{6}", e), f"formato raro: {e}"


def test_granada_aparece_en_los_dos_anios():
    """Es el hallazgo que destaca el texto; si deja de ser cierto al
    actualizar los datos, hay que quitar la frase."""
    det = _bloque().split('<details')
    assert "Granada" in det[1] and "Granada" in det[2]
    assert "Granada aparece en las dos listas" in _texto_plano()


def test_se_cita_la_fuente_y_la_fecha():
    """Sin fecha el dato no vale: la revisión sigue abierta."""
    texto = _texto_plano()
    assert "Secretaría de Estado de Derechos Sociales" in texto
    assert "9 de septiembre de 2026" in texto


def test_se_avisa_de_que_los_datos_son_provisionales():
    """Los tres «ninguna» se leen como un cierre y no lo son.

    Cuando se respondió, la revisión de las cuentas justificativas seguía
    abierta y de 2025 solo se contestaron dos de las cuatro preguntas. Sin
    este aviso, la página estaría dando por cerrado algo que sigue en curso.
    """
    texto = _texto_plano()
    assert "provisionales" in texto
    assert "2025" in texto and "en ejecución" in texto
    assert "Seguimos pidiendo la información actualizada" in texto


def test_se_explica_que_no_justificar_lleva_a_reintegro():
    """Es lo que convierte la lista en relevante y no en una anécdota: el
    siguiente paso de quien no arregla los papeles está en la ley."""
    texto = _texto_plano()
    assert "causa de\n reintegro" in texto or "causa de reintegro" in texto
    assert "Ley 38/2003" in texto and "37.1.c" in texto


def test_las_dos_entidades_que_regularizaron_se_marcan():
    """Granada y Puigverd de Lérida sí justificaron tras el requerimiento.
    Dejarlas en la lista a secas las trataría igual que a las demás."""
    det = _bloque().split('<details')[1]
    assert det.count('justif__ok') == 2
    assert "Puigverd de Lérida" in det


def test_no_hay_estilos_en_linea():
    """Regla del proyecto: las clases van en styles.css."""
    assert 'style="' not in _bloque()


def test_las_clases_tienen_estilo_definido():
    for clase in set(re.findall(r"justif__[a-z]+", _bloque())):
        assert f".{clase}" in CSS, f"falta .{clase} en styles.css"


def test_el_texto_es_legible():
    """Suelo de 0.875rem para texto corrido, que es criterio del sitio.
    Se permite menos solo en el número de expediente y la etiqueta verde,
    que son apoyos y no texto que haya que leer seguido.
    """
    bloque_css = CSS[CSS.index("JUSTIFICACIÓN DE LAS AYUDAS"):]
    medidas = 0
    for selector, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", bloque_css):
        selector = selector.strip()
        if "justif__" not in selector:
            continue
        # Los pseudoelementos (el triángulo ▶ del desplegable) no son texto.
        if "::" in selector:
            continue
        # El expediente y la etiqueta verde son apoyos, no texto corrido.
        if "justif__exp" in selector or "justif__ok" in selector:
            continue
        tam = re.search(r"font-size:\s*([\d.]+)rem", cuerpo)
        if not tam:
            continue
        medidas += 1
        assert float(tam.group(1)) >= 0.875, \
            f"{selector} va a {tam.group(1)}rem, por debajo del suelo"
    assert medidas >= 3, "no se ha medido casi nada: ¿cambió el nombre del bloque?"


def test_se_cuenta_que_hubo_que_reclamar_las_dos_veces():
    """No es una queja decorativa: es la parte práctica del bloque.

    Quien lea esto y quiera pedir sus propios datos necesita saber que la
    primera respuesta puede ser un «está en revisión» y que reclamar funciona.
    Sin esto, el bloque es un dato; con esto, es algo que otra persona puede
    repetir.
    """
    texto = _texto_plano()
    assert "Consejo de Transparencia y Buen Gobierno" in texto
    assert "no es un caso aislado" in texto.lower()
    assert "las dos veces la reclamación prosperó" in texto
    assert 'href="recursos.html"' in _bloque(), "falta el enlace al cómo"
