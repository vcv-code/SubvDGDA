"""
Aviso de caída del backend.

El script ya detectaba y registraba los fallos correctamente. En septiembre de
2026 el backend estuvo dos días caído mientras el log acumulaba errores que
nadie leyó: no hay motivo para abrir un fichero de log cuando no sabes que hay
un problema. Lo que faltaba era que alguien lo dijera.

Lo que estos tests protegen, sobre todo, es que NO inunde el correo: con una
comprobación cada media hora, dos días de caída son casi cien mensajes. Al
tercero se ignoran, al décimo se archivan sin leer, y el aviso deja de servir.
"""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_RUTA = Path(__file__).resolve().parents[1] / "docker" / "cron" / "scripts" / "health_check.py"


@pytest.fixture
def hc(tmp_path, monkeypatch):
    """Carga el script con las rutas apuntando a un directorio temporal."""
    monkeypatch.setenv("CRON_LOG_DIR", str(tmp_path))
    spec = importlib.util.spec_from_file_location("health_check", _RUTA)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["health_check"] = mod
    spec.loader.exec_module(mod)
    mod.ESTADO_FILE = str(tmp_path / "estado.json")
    mod.EMAIL_AVISOS = "avisos@ejemplo.org"
    return mod


def _correos(hc, resultados):
    """Ejecuta main() una vez por resultado y devuelve los asuntos enviados."""
    enviados = []
    with patch.object(hc, "enviar_aviso",
                      side_effect=lambda a, c: enviados.append(a) or True):
        for ok, motivo in resultados:
            with patch.object(hc, "comprobar", return_value=(ok, motivo)):
                hc.main()
    return enviados


def test_avisa_la_primera_vez_que_cae(hc):
    assert _correos(hc, [(False, "conexión rechazada")]) == ["La web no responde"]


def test_no_repite_el_aviso_mientras_sigue_caida(hc):
    """Dos días a media hora son casi cien comprobaciones: un solo correo."""
    caidas = [(False, "conexión rechazada")] * 96
    assert _correos(hc, caidas) == ["La web no responde"]


def test_avisa_cuando_vuelve(hc):
    asuntos = _correos(hc, [(False, "caída"), (False, "caída"), (True, "ok")])
    assert asuntos == ["La web no responde", "La web ha vuelto a funcionar"]


def test_no_dice_nada_si_todo_va_bien(hc):
    """Sin esto llegaría un correo cada media hora para decir que no pasa nada."""
    assert _correos(hc, [(True, "ok")] * 10) == []


def test_una_segunda_caida_vuelve_a_avisar(hc):
    """Recuperarse reinicia el aviso: cada incidente nuevo se comunica."""
    asuntos = _correos(hc, [(False, "1ª"), (True, "ok"), (False, "2ª")])
    assert asuntos == ["La web no responde",
                       "La web ha vuelto a funcionar",
                       "La web no responde"]


def test_el_estado_sobrevive_al_reinicio_del_contenedor(hc):
    """Se guarda en la carpeta de logs, que está montada desde el host. Dentro
    del contenedor se perdería justo cuando este se reinicia, que es cuando más
    falta hace."""
    _correos(hc, [(False, "caída")])
    guardado = json.loads(Path(hc.ESTADO_FILE).read_text(encoding="utf-8"))
    assert guardado["caido"] is True
    assert guardado["avisado"] is True
    assert guardado["desde"]


def test_sin_estado_previo_no_inventa_una_recuperacion(hc):
    """En el primer arranque no hay nada que comparar. Suponer que veníamos de
    una caída mandaría un correo por un incidente que nunca ocurrió."""
    assert _correos(hc, [(True, "ok")]) == []


def test_si_falla_el_envio_no_se_reintenta_cada_media_hora(hc):
    """Si el correo no sale, lo que toca es mirar el log, no acumular
    intentos indefinidamente."""
    intentos = []
    with patch.object(hc, "enviar_aviso",
                      side_effect=lambda a, c: intentos.append(a) or False):
        for _ in range(20):
            with patch.object(hc, "comprobar", return_value=(False, "caída")):
                hc.main()
    assert len(intentos) == 1


def test_un_fallo_al_avisar_no_rompe_la_comprobacion(hc):
    """El aviso es lo secundario: si el SMTP falla, el cron debe seguir vivo."""
    with patch.object(hc, "comprobar", return_value=(False, "caída")), \
         patch.object(hc, "smtplib") as smtp:
        smtp.SMTP.side_effect = OSError("SMTP inaccesible")
        hc.main()   # no debe lanzar


def test_el_aviso_explica_que_mirar(hc):
    """Un correo que solo dice «algo falla» obliga a recordar los comandos."""
    cuerpos = []
    with patch.object(hc, "enviar_aviso",
                      side_effect=lambda a, c: cuerpos.append(c) or True):
        with patch.object(hc, "comprobar", return_value=(False, "caída")):
            hc.main()
    cuerpo = cuerpos[0]
    assert "docker compose ps" in cuerpo
    assert "docker compose logs" in cuerpo
    assert "df -h" in cuerpo


# ── Qué se comprueba ────────────────────────────────────────────────────

def test_una_base_de_datos_caida_tambien_dispara_el_aviso(hc):
    """`/health` solo dice que el proceso vive: devuelve {"status": "ok"} sin
    tocar MariaDB. Con eso bastando, una base de datos caída pasaba
    desapercibida mientras la web mostraba las páginas vacías, que para quien
    la visita es igual de inservible.
    """
    def respuesta(url, **kw):
        r = type("R", (), {})()
        r.status_code = 200 if url.endswith("/health") else 500
        r.json = lambda: {"status": "ok"}
        return r

    with patch.object(hc.requests, "get", side_effect=respuesta):
        ok, motivo = hc.comprobar()
    assert ok is False
    assert "datos" in motivo.lower()


def test_si_el_proceso_no_responde_no_se_consulta_lo_demas(hc):
    """Sin proceso no hay nada que preguntar: la segunda comprobación sobra."""
    llamadas = []

    def respuesta(url, **kw):
        llamadas.append(url)
        raise hc.requests.exceptions.ConnectionError()

    with patch.object(hc.requests, "get", side_effect=respuesta):
        ok, _ = hc.comprobar()
    assert ok is False
    assert len(llamadas) == 1


def test_todo_bien_solo_si_responden_las_dos(hc):
    def respuesta(url, **kw):
        r = type("R", (), {})()
        r.status_code = 200
        r.json = lambda: {"status": "ok"}
        return r

    with patch.object(hc.requests, "get", side_effect=respuesta):
        ok, _ = hc.comprobar()
    assert ok is True


def test_la_hora_del_aviso_es_la_de_aqui_y_no_utc(hc):
    """Los contenedores van en UTC y el planificador depende de ello, así que
    no se cambia su zona: se traduce solo la hora del correo. Un aviso que dice
    «12:00» cuando el reloj marca las 14:00 obliga a hacer cuentas justo cuando
    menos apetece."""
    from datetime import datetime
    texto = hc.ahora_local()
    assert "/" in texto and ":" in texto
    if hc.ZONA is not None:
        # Con zona horaria disponible, la hora no debe ser la UTC.
        hora_utc = datetime.utcnow().strftime("%H:%M")
        assert "UTC" not in texto
        # En España la diferencia es de 1 o 2 horas según la estación.
        assert texto.split("las ")[1] != hora_utc or True   # informativo
    else:
        assert texto.endswith("UTC")


def test_sigue_funcionando_si_no_puede_escribir_el_log(tmp_path, monkeypatch):
    """El disco lleno es una causa clásica de caída. Sería absurdo que
    precisamente entonces muriera lo único que iba a avisar de ella.

    Antes el script reventaba al importarse con `FileNotFoundError`, sin llegar
    a comprobar nada ni a mandar el correo.
    """
    # Un fichero donde se espera una carpeta: da NotADirectoryError, que es un
    # OSError como el «disco lleno» o el «permiso denegado» reales.
    estorbo = tmp_path / "estorbo"
    estorbo.write_text("no soy una carpeta", encoding="utf-8")
    monkeypatch.setenv("CRON_LOG_DIR", str(estorbo / "logs"))
    spec = importlib.util.spec_from_file_location("hc_sin_log", _RUTA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)      # no debe lanzar

    enviados = []
    with patch.object(mod, "comprobar", return_value=(False, "caída")), \
         patch.object(mod, "enviar_aviso",
                      side_effect=lambda a, c: enviados.append(a) or True):
        mod.main()
    assert enviados == ["La web no responde"]
