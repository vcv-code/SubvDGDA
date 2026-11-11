"""
Recordatorio semestral para refrescar la tabla de licitaciones.

Por qué existe este test
------------------------
La web publica una tabla de contratos públicos con una fecha visible, y eso solo
es honesto si alguien la actualiza. El recordatorio es lo que hace que ese
«alguien» no dependa de acordarse. Dos cosas pueden romperlo en silencio:

1. **Que el correo mienta sobre la antigüedad.** La fecha no está escrita en el
   script: se lee de la nota al pie de `recursos.html`. Si alguien reescribe esa
   frase al publicar una tabla nueva, el aviso debe decir que no la encuentra,
   no inventarse una.

2. **Que el correo deje de decir qué hacer.** Un recordatorio que llega cada seis
   meses y no recuerda los pasos obliga a reconstruirlos cada vez, y entonces se
   pospone.
"""
import importlib.util
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent.parent
SCRIPT = RAIZ / "scripts" / "recordatorio_licitaciones.py"


def _modulo():
    spec = importlib.util.spec_from_file_location("recordatorio", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_el_script_existe():
    assert SCRIPT.exists(), "Falta scripts/recordatorio_licitaciones.py"


def test_lee_la_fecha_de_la_web_y_no_la_lleva_escrita():
    """Si estuviera escrita aquí, al publicar una tabla nueva habría que tocar
    dos sitios y el correo acabaría mintiendo."""
    m = _modulo()
    pub = m.fecha_publicada()
    assert pub is not None, (
        "No se encuentra «Datos a <mes> de <año>» en recursos.html: el "
        "recordatorio no sabría decir de cuándo son los datos publicados."
    )
    mes, anio = pub
    assert mes in m.MESES and 2020 <= anio <= 2100
    texto = SCRIPT.read_text(encoding="utf-8")
    assert f"Datos a {mes} de {anio}" not in texto, "la fecha está duplicada en el script"


def test_dice_cuantos_meses_han_pasado():
    m = _modulo()
    assert m._meses_desde("noviembre", 2026, date(2027, 1, 15)) == 2
    assert m._meses_desde("noviembre", 2026, date(2027, 7, 15)) == 8
    assert m._meses_desde("enero", 2026, date(2026, 1, 20)) == 0


def test_el_correo_recuerda_los_pasos_y_la_ruta_del_pdf():
    """Que no haya que reconstruir el procedimiento cada seis meses."""
    m = _modulo()
    _, cuerpo = m.componer(hoy=date(2027, 7, 15))
    assert "licitaciones-pienso-colonias-municipios.pdf" in cuerpo
    assert "recursos.html" in cuerpo
    assert "contrataciondelestado.es" in cuerpo
    assert "8 meses" in cuerpo, "no dice cuánto llevan los datos sin actualizar"


def test_avisa_si_no_puede_leer_la_fecha(monkeypatch):
    """Mejor un aviso raro que una antigüedad inventada."""
    m = _modulo()
    monkeypatch.setattr(m, "fecha_publicada", lambda: None)
    _, cuerpo = m.componer(hoy=date(2027, 1, 15))
    assert "AVISO" in cuerpo and "recursos.html" in cuerpo


def test_el_remitente_lo_distingue_del_aviso_de_visitas():
    """Los dos salen del mismo servidor y del mismo código de envío; si llegan
    con el mismo nombre, en la bandeja parecen el mismo aviso repetido."""
    assert 'etiqueta="licitaciones"' in SCRIPT.read_text(encoding="utf-8")
    envio = (RAIZ / "scripts" / "aviso_visitas.py").read_text(encoding="utf-8")
    assert "def enviar(asunto, cuerpo, etiqueta=" in envio
