"""
Tests del formulario de contacto (POST /contacto/).

Cubren el envío correcto, el honeypot, la validación de entrada, el fallo
de SMTP (503) y la configuración de rate limiting en Nginx.
"""
import smtplib
from pathlib import Path
from unittest.mock import patch

NGINX_CONF = Path(__file__).parent.parent / "docker/nginx/default.conf"

MENSAJE_OK = {
    "nombre":  "Vero",
    "email":   "vero@ejemplo.com",
    "mensaje": "Hola, tengo una duda sobre las convocatorias EPA.",
}


# ── Envío correcto ──────────────────────────────────────────────────────────

def test_contacto_valido_envia_email(client):
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=MENSAJE_OK)
    assert r.status_code == 200
    assert "mensaje" in r.json()
    mock_enviar.assert_called_once_with(
        MENSAJE_OK["nombre"], MENSAJE_OK["email"], MENSAJE_OK["mensaje"]
    )


def test_contacto_recorta_espacios(client):
    """nombre/mensaje llegan al email sin espacios sobrantes (validadores .strip())."""
    datos = {"nombre": "  Vero  ", "email": "vero@ejemplo.com",
             "mensaje": "   Mensaje con espacios alrededor.   "}
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=datos)
    assert r.status_code == 200
    nombre, _, mensaje = mock_enviar.call_args[0]
    assert nombre == "Vero"
    assert mensaje == "Mensaje con espacios alrededor."


# ── Honeypot ────────────────────────────────────────────────────────────────

def test_contacto_honeypot_no_envia(client):
    """Si el campo trampa llega relleno, se devuelve éxito falso sin enviar nada."""
    datos = {**MENSAJE_OK, "sitio_web": "http://spam.example"}
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=datos)
    assert r.status_code == 200
    assert "mensaje" in r.json()
    mock_enviar.assert_not_called()


# ── Validación de entrada (422) ─────────────────────────────────────────────

def test_contacto_mensaje_corto_422(client):
    datos = {**MENSAJE_OK, "mensaje": "corto"}
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=datos)
    assert r.status_code == 422
    mock_enviar.assert_not_called()


def test_contacto_email_invalido_422(client):
    datos = {**MENSAJE_OK, "email": "no-es-un-email"}
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=datos)
    assert r.status_code == 422
    mock_enviar.assert_not_called()


def test_contacto_nombre_opcional(client):
    """El nombre es opcional: sin nombre, el mensaje se envía igual."""
    datos = {"email": "vero@ejemplo.com", "mensaje": "Mensaje sin nombre indicado."}
    with patch("backend.app.routers.contacto.enviar_email_contacto") as mock_enviar:
        r = client.post("/contacto/", json=datos)
    assert r.status_code == 200
    nombre, _, _ = mock_enviar.call_args[0]
    assert nombre == ""


# ── Fallo de SMTP (503) ─────────────────────────────────────────────────────

def test_contacto_smtp_error_503(client):
    with patch("backend.app.routers.contacto.enviar_email_contacto",
               side_effect=smtplib.SMTPException("smtp caído")):
        r = client.post("/contacto/", json=MENSAJE_OK)
    assert r.status_code == 503


# ── Configuración de rate limiting en Nginx ─────────────────────────────────

def test_nginx_zona_contacto_definida():
    contenido = NGINX_CONF.read_text()
    assert "zone=contacto" in contenido


def test_nginx_rate_limit_aplicado_a_contacto():
    contenido = NGINX_CONF.read_text()
    assert "/contacto/" in contenido
    assert "limit_req" in contenido
