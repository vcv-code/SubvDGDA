"""
Tests del modo mantenimiento.

No requieren Docker: verifican la configuración de Nginx y la existencia
de la página de mantenimiento localmente.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
NGINX_CONF = ROOT / "docker/nginx/default.conf"
MANTEN_HTML = ROOT / "frontend/mantenimiento.html"


def test_nginx_comprueba_bandera_mantenimiento():
    contenido = NGINX_CONF.read_text()
    assert "maintenance.on" in contenido


def test_nginx_503_sirve_pagina_mantenimiento():
    contenido = NGINX_CONF.read_text()
    assert "error_page 503" in contenido
    assert "/mantenimiento.html" in contenido


def test_nginx_503_separado_de_los_errores_de_servidor():
    """El 503 (mantenimiento) ya no comparte línea con 50x.html (500/502/504)."""
    contenido = NGINX_CONF.read_text()
    assert "error_page 500 502 504" in contenido
    assert "error_page 500 502 503 504" not in contenido


def test_pagina_mantenimiento_existe_y_tiene_contenido():
    assert MANTEN_HTML.is_file()
    html = MANTEN_HTML.read_text().lower()
    assert "mantenimiento" in html
    assert "noindex" in html  # no debe indexarse en buscadores
