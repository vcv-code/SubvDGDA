"""
Tests de configuración HTTPS.
No requieren Docker ni conexión de red — verifican los archivos localmente.
"""
import subprocess
from pathlib import Path

CERT_PATH = Path(__file__).parent.parent / "docker/ssl/server.crt"
KEY_PATH  = Path(__file__).parent.parent / "docker/ssl/server.key"
NGINX_CONF = Path(__file__).parent.parent / "docker/nginx/default.conf"


def test_certificado_existe():
    assert CERT_PATH.exists(), "server.crt no encontrado — ejecuta el comando openssl de docs/https.md"


def test_clave_excluida_de_git():
    gitignore = Path(__file__).parent.parent / ".gitignore"
    contenido = gitignore.read_text()
    assert "server.key" in contenido


def test_certificado_dominio_correcto():
    result = subprocess.run(
        ["openssl", "x509", "-in", str(CERT_PATH), "-noout", "-subject"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "subvencionesDGDA.local" in result.stdout


def test_certificado_san_incluido():
    result = subprocess.run(
        ["openssl", "x509", "-in", str(CERT_PATH), "-noout", "-ext", "subjectAltName"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "subvencionesDGDA.local" in result.stdout


def test_certificado_no_expirado():
    result = subprocess.run(
        ["openssl", "x509", "-in", str(CERT_PATH), "-noout", "-checkend", "0"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, "El certificado ha expirado"


def test_nginx_conf_escucha_443():
    contenido = NGINX_CONF.read_text()
    assert "listen 443 ssl" in contenido


def test_nginx_conf_redirige_http():
    contenido = NGINX_CONF.read_text()
    assert "return 301 https://" in contenido


def test_nginx_conf_hsts():
    contenido = NGINX_CONF.read_text()
    assert "Strict-Transport-Security" in contenido


def test_nginx_conf_tls_moderno():
    contenido = NGINX_CONF.read_text()
    assert "TLSv1.2" in contenido
    assert "TLSv1.3" in contenido
