import logging
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
