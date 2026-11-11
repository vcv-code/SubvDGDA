"""
Aviso para volver a preguntar por las justificaciones de las EELL.

Lo que se vigila aquí es que el recordatorio siga sabiendo DE CUÁNDO son los
datos publicados. La fecha no está escrita en el script: se lee de la página.
Es lo correcto —así se entera solo cuando se publiquen datos nuevos— pero
depende de una frase concreta del HTML, y si alguien la reescribe el aviso se
queda mudo sin que nadie se entere hasta dentro de seis meses.
"""
import importlib.util
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "recordatorio_transparencia",
        RAIZ / "scripts" / "recordatorio_transparencia.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _modulo()


def test_lee_la_fecha_de_la_pagina():
    """Si esto falla, lo más probable es que se haya reescrito la entradilla
    del bloque en estadisticas-eell.html."""
    pub = MOD.fecha_publicada()
    assert pub is not None, "no se encuentra «A <día> de <mes> de <año> respondió»"
    mes, anio = pub
    assert mes in MOD.MESES
    assert 2026 <= anio <= 2100


def test_el_correo_dice_cuanto_tiempo_lleva():
    """El dato útil no es la fecha, es la antigüedad: «hace 14 meses» mueve a
    actuar y «septiembre de 2026» no."""
    mes, anio = MOD.fecha_publicada()
    i = MOD.MESES.index(mes)
    futuro = date(anio + 1, i + 1, 15)
    _, cuerpo = MOD.componer(hoy=futuro)
    assert "hace 12 meses" in cuerpo


def test_avisa_en_vez_de_inventarse_la_fecha(tmp_path, monkeypatch):
    """Si no puede leerla, el correo tiene que decirlo. Callar y mandar el
    recordatorio a secas haría pensar que no hay nada que revisar."""
    vacia = tmp_path / "pagina.html"
    vacia.write_text("<p>sin la frase de siempre</p>", encoding="utf-8")
    monkeypatch.setattr(MOD, "PAGINA", vacia)
    assert MOD.fecha_publicada() is None
    _, cuerpo = MOD.componer()
    assert "AVISO:" in cuerpo


def test_recuerda_que_el_cero_de_reintegros_es_provisional():
    """Es el motivo de que exista este recordatorio. Sin esta frase, quien lo
    reciba dentro de un año puede pensar que el asunto está cerrado."""
    _, cuerpo = MOD.componer()
    assert "causa de reintegro" in cuerpo
    assert "Ley 38/2003" in cuerpo


def test_enumera_lo_que_hay_que_volver_a_preguntar():
    """Que no haya que reconstruir la solicitud de memoria dentro de un año."""
    _, cuerpo = MOD.componer()
    for punto in ("renuncian", "derecho al cobro", "devolución voluntaria",
                  "reintegro", "no han presentado la justificación",
                  "estado de tramitación"):
        assert punto in cuerpo, f"falta: {punto}"


def test_no_lleva_datos_personales():
    """El repositorio va a hacerse público.

    La solicitud y la reclamación van a nombre de una persona física, y sus
    números permiten llegar a ella desde el buscador del Consejo de
    Transparencia. El recordatorio no los necesita para nada.
    """
    fuente = (RAIZ / "scripts" / "recordatorio_transparencia.py").read_text(
        encoding="utf-8")
    _, cuerpo = MOD.componer()
    for dato in ("Corpa", "Vaquero", "2682/2026", "AC2000000686237", "686237"):
        assert dato not in fuente, f"dato personal en el script: {dato}"
        assert dato not in cuerpo, f"dato personal en el correo: {dato}"


def test_se_distingue_del_otro_recordatorio_en_la_bandeja():
    """Hay dos avisos semestrales distintos. Si ambos llegan con el mismo
    remitente y asuntos parecidos, acaban leyéndose como uno repetido."""
    asunto, _ = MOD.componer()
    otro = RAIZ / "scripts" / "recordatorio_licitaciones.py"
    assert "licitaciones" not in asunto.lower()
    assert 'etiqueta="transparencia"' in (
        RAIZ / "scripts" / "recordatorio_transparencia.py").read_text(encoding="utf-8")
    assert 'etiqueta="licitaciones"' in otro.read_text(encoding="utf-8")
