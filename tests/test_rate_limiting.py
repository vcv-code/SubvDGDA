"""
Tests de configuración de rate limiting.
No requieren Docker — verifican el archivo de configuración Nginx localmente.
"""
from pathlib import Path

NGINX_CONF = Path(__file__).parent.parent / "docker/nginx/default.conf"


def test_nginx_tiene_limit_req_zone():
    contenido = NGINX_CONF.read_text()
    assert "limit_req_zone" in contenido


def test_nginx_zona_login_definida():
    contenido = NGINX_CONF.read_text()
    assert "zone=login" in contenido


def test_nginx_rate_10_por_minuto():
    contenido = NGINX_CONF.read_text()
    assert "10r/m" in contenido


def test_nginx_status_429():
    contenido = NGINX_CONF.read_text()
    assert "429" in contenido


def test_nginx_rate_limit_aplicado_a_login():
    contenido = NGINX_CONF.read_text()
    assert "/auth/login" in contenido
    assert "limit_req" in contenido


def test_nginx_sin_zona_ni_rate_limit_de_registro():
    """El alta pública ya no existe, así que su zona tampoco debe quedarse.

    Una zona `limit_req_zone` huérfana reserva 10 MB de memoria compartida en
    Nginx sin que ninguna `location` la use.
    """
    contenido = NGINX_CONF.read_text()
    assert "zone=registro" not in contenido
    assert "/auth/registro" not in contenido
