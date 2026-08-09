import logging
from pathlib import Path
from unittest.mock import patch


def test_middleware_registra_request(client, caplog):
    with caplog.at_level(logging.INFO, logger="bdns"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any("GET" in r.message and "/health" in r.message for r in caplog.records)


def test_middleware_registra_codigo_respuesta(client, caplog):
    with caplog.at_level(logging.INFO, logger="bdns"):
        client.get("/ruta-que-no-existe-404")

    assert any("404" in r.message for r in caplog.records)


def test_middleware_registra_ip(client, caplog):
    with caplog.at_level(logging.INFO, logger="bdns"):
        client.get("/health")

    assert any("testclient" in r.message or "127.0.0.1" in r.message for r in caplog.records)


def test_exception_handler_loguea_error(caplog):
    """El generic_exception_handler debe llamar a logger.error con el tipo y mensaje."""
    import asyncio
    import backend.app.main as main_module
    from unittest.mock import MagicMock
    from starlette.requests import Request

    mock_logger = MagicMock()
    original = main_module.logger
    main_module.logger = mock_logger

    try:
        scope = {
            "type": "http", "method": "GET", "path": "/test",
            "query_string": b"", "headers": [],
        }
        request = Request(scope)
        asyncio.run(main_module.generic_exception_handler(request, ValueError("error forzado")))
        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        assert "ValueError" in args or any("ValueError" in str(a) for a in args)
    finally:
        main_module.logger = original


def test_setup_logging_configura_handlers():
    from backend.app.logger import setup_logging

    logger = setup_logging()

    assert logger.name == "bdns"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


# ── Formato de los registros de Nginx ────────────────────────────────────────
# Estos logs no los lee ningún código del proyecto: son la materia prima para
# analizar las visitas. Los tests protegen los dos campos que se añadieron para
# eso, porque una vuelta atrás no rompería nada y pasaría inadvertida hasta que
# hiciera falta el dato — y para entonces esos meses ya estarían perdidos.

NGINX_CONF = Path(__file__).parent.parent / "docker/nginx/default.conf"


def _log_format():
    conf = NGINX_CONF.read_text(encoding="utf-8")
    inicio = conf.index("log_format bdns")
    return conf[inicio:conf.index(";", inicio)]


def test_log_format_registra_la_procedencia():
    """Sin referrer no se puede saber de dónde llegan los visitantes."""
    assert "$http_referer" in _log_format()


def test_log_format_registra_el_dispositivo():
    """Sin user-agent no se puede distinguir móvil de escritorio."""
    assert "$http_user_agent" in _log_format()


def test_log_format_conserva_ip_estado_y_tiempo():
    formato = _log_format()
    for campo in ("$remote_addr", "$status", "$request_time"):
        assert campo in formato, campo


PRIVACIDAD = Path(__file__).parent.parent / "frontend/privacidad.html"


def _seccion_registros_del_servidor():
    """Solo esa sección de privacidad.html, con los espacios normalizados.

    Se acota a la sección porque buscar en el documento entero daría falsos
    positivos: "navegador" y "dirección IP" aparecen también en el apartado de
    los CDN, así que el test pasaría aunque se borrase lo que aquí se comprueba.

    Y se normalizan los espacios porque el HTML parte las frases en varias
    líneas con sangría: comparando en crudo, el test se rompería solo con
    reformatear el párrafo, sin que hubiera cambiado nada de lo que declara.
    """
    html = PRIVACIDAD.read_text(encoding="utf-8")
    inicio = html.index("Registros del servidor")
    return " ".join(html[inicio:html.index("</section>", inicio)].split())


def test_la_politica_de_privacidad_declara_lo_que_se_registra():
    """La IP es dato personal: lo que se anota tiene que estar declarado."""
    seccion = _seccion_registros_del_servidor()
    for declarado in ("dirección IP",
                      "la página desde la que se llegó",
                      "el navegador y sistema operativo utilizados"):
        assert declarado in seccion, declarado


def test_la_politica_de_privacidad_mantiene_el_plazo_de_conservacion():
    """Sin plazo declarado, la sección quedaría incompleta frente al RGPD."""
    assert "30 días" in _seccion_registros_del_servidor()
