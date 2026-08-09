"""
Tests de la configuración de correo saliente (backend/app/auth.py).

El objetivo de estos tests es doble: comprobar que el envío a un proveedor
real (con STARTTLS y usuario/contraseña) se hace como toca, y sobre todo que
los valores por defecto siguen siendo los de Mailpit, para que el entorno de
desarrollo no dependa de configurar nada.
"""
import importlib
import os
import smtplib
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

import backend.app.auth as auth


def _mensaje():
    msg = EmailMessage()
    msg["Subject"] = "Prueba"
    msg["From"] = "de@ejemplo.com"
    msg["To"] = "para@ejemplo.com"
    msg.set_content("Cuerpo")
    return msg


def _servidor_simulado(mock_smtp):
    """Devuelve el objeto que `with smtplib.SMTP(...) as servidor` entrega."""
    return mock_smtp.return_value.__enter__.return_value


# ── Comportamiento por defecto: Mailpit ─────────────────────────────────────

def test_por_defecto_no_cifra_ni_autentica():
    """Sin variables de entorno el envío es en claro, como espera Mailpit."""
    with patch("backend.app.auth.smtplib.SMTP") as mock_smtp:
        auth._entregar_mensaje(_mensaje())

    servidor = _servidor_simulado(mock_smtp)
    servidor.starttls.assert_not_called()
    servidor.login.assert_not_called()
    servidor.send_message.assert_called_once()


def test_se_conecta_al_host_y_puerto_configurados():
    with patch("backend.app.auth.smtplib.SMTP") as mock_smtp:
        auth._entregar_mensaje(_mensaje())

    mock_smtp.assert_called_once_with(
        auth.SMTP_HOST, auth.SMTP_PORT, timeout=auth.SMTP_TIMEOUT
    )


def test_hay_timeout_configurado():
    """Sin timeout, un SMTP que acepta y no responde colgaría la petición."""
    assert auth.SMTP_TIMEOUT > 0


# ── Comportamiento en producción: TLS y credenciales ────────────────────────

def test_con_tls_activado_llama_a_starttls():
    with patch("backend.app.auth.SMTP_TLS", True), \
         patch("backend.app.auth.smtplib.SMTP") as mock_smtp:
        auth._entregar_mensaje(_mensaje())

    _servidor_simulado(mock_smtp).starttls.assert_called_once()


def test_con_usuario_configurado_hace_login():
    with patch("backend.app.auth.SMTP_USER", "cuenta@gmail.com"), \
         patch("backend.app.auth.SMTP_PASSWORD", "secreto"), \
         patch("backend.app.auth.smtplib.SMTP") as mock_smtp:
        auth._entregar_mensaje(_mensaje())

    _servidor_simulado(mock_smtp).login.assert_called_once_with(
        "cuenta@gmail.com", "secreto"
    )


def test_starttls_va_antes_del_login():
    """Autenticar antes de cifrar enviaría la contraseña en claro."""
    orden = []
    with patch("backend.app.auth.SMTP_TLS", True), \
         patch("backend.app.auth.SMTP_USER", "cuenta@gmail.com"), \
         patch("backend.app.auth.smtplib.SMTP") as mock_smtp:
        servidor = _servidor_simulado(mock_smtp)
        servidor.starttls = MagicMock(side_effect=lambda *a, **k: orden.append("tls"))
        servidor.login = MagicMock(side_effect=lambda *a, **k: orden.append("login"))
        auth._entregar_mensaje(_mensaje())

    assert orden == ["tls", "login"]


# ── Enlaces de los correos ──────────────────────────────────────────────────

def test_enlace_de_verificacion_usa_site_url():
    with patch("backend.app.auth.SITE_URL", "https://ejemplo.org"), \
         patch("backend.app.auth._entregar_mensaje") as mock_entregar:
        auth.enviar_email_verificacion("alguien@ejemplo.com", "tok123")

    cuerpo = mock_entregar.call_args[0][0].get_content()
    assert "https://ejemplo.org/verificar-email.html?token=tok123" in cuerpo


def test_enlace_de_recuperacion_usa_site_url():
    with patch("backend.app.auth.SITE_URL", "https://ejemplo.org"), \
         patch("backend.app.auth._entregar_mensaje") as mock_entregar:
        auth.enviar_email_recuperacion("alguien@ejemplo.com", "tok456")

    cuerpo = mock_entregar.call_args[0][0].get_content()
    assert "https://ejemplo.org/reset-password.html?token=tok456" in cuerpo


# ── Lectura de variables de entorno ─────────────────────────────────────────

def _recargar_con(entorno):
    """Reimporta auth.py con el entorno indicado y deja el módulo como estaba.

    El try/finally no es decorativo: si la recarga fallara, el módulo quedaría
    con la configuración de prueba y arrastraría el fallo al resto de tests.
    """
    try:
        with patch.dict(os.environ, entorno, clear=False):
            recargado = importlib.reload(auth)
            return {
                "host": recargado.SMTP_HOST,
                "port": recargado.SMTP_PORT,
                "tls": recargado.SMTP_TLS,
                "from": recargado.EMAIL_FROM,
                "contacto": recargado.EMAIL_CONTACTO,
                "site": recargado.SITE_URL,
            }
    finally:
        importlib.reload(auth)


def test_variables_vacias_caen_al_valor_por_defecto():
    """Docker compose propaga las variables no definidas como cadena vacía."""
    valores = _recargar_con({
        "SMTP_HOST": "", "SMTP_PORT": "", "EMAIL_FROM": "",
        "EMAIL_CONTACTO": "", "SITE_URL": "",
    })
    assert valores["host"] == "localhost"
    assert valores["port"] == 1025
    assert valores["from"] == "noreply@subvencionesDGDA.local"
    assert valores["contacto"] == valores["from"]
    assert valores["site"] == "https://subvencionesDGDA.local"


def test_site_url_ignora_la_barra_final():
    """Con barra final se compondrían enlaces con doble barra."""
    assert _recargar_con({"SITE_URL": "https://ejemplo.org/"})["site"] == "https://ejemplo.org"


def test_smtp_tls_acepta_las_formas_habituales_de_decir_si():
    for valor in ("true", "True", "1", "yes", "si", "sí"):
        assert _recargar_con({"SMTP_TLS": valor})["tls"] is True, valor
    for valor in ("false", "0", "no", ""):
        assert _recargar_con({"SMTP_TLS": valor})["tls"] is False, valor


def test_email_contacto_puede_diferir_del_remitente():
    valores = _recargar_con({
        "EMAIL_FROM": "noreply@ejemplo.org",
        "EMAIL_CONTACTO": "buzon@ejemplo.org",
    })
    assert valores["from"] == "noreply@ejemplo.org"
    assert valores["contacto"] == "buzon@ejemplo.org"


def test_el_mensaje_de_contacto_va_al_buzon_configurado():
    """Con Reply-To al visitante, para que responder no revele el buzón."""
    with patch("backend.app.auth.EMAIL_CONTACTO", "buzon@ejemplo.org"), \
         patch("backend.app.auth._entregar_mensaje") as mock_entregar:
        auth.enviar_email_contacto("Vero", "visitante@ejemplo.com", "Hola")

    msg = mock_entregar.call_args[0][0]
    assert msg["To"] == "buzon@ejemplo.org"
    assert msg["Reply-To"] == "visitante@ejemplo.com"


# ── Tolerancia a fallos ─────────────────────────────────────────────────────

def test_fallo_de_conexion_no_tumba_la_recuperacion():
    """Una conexión rechazada es OSError, no SMTPException: antes daba error 500."""
    with patch("backend.app.auth._entregar_mensaje",
               side_effect=ConnectionRefusedError("sin SMTP")):
        auth.enviar_email_recuperacion("alguien@ejemplo.com", "tok")


def test_fallo_de_smtp_no_tumba_la_verificacion():
    with patch("backend.app.auth._entregar_mensaje",
               side_effect=smtplib.SMTPException("rechazado")):
        auth.enviar_email_verificacion("alguien@ejemplo.com", "tok")


def test_contacto_si_propaga_el_error():
    """El formulario debe avisar de que no se envió, no fingir éxito."""
    with patch("backend.app.auth._entregar_mensaje",
               side_effect=smtplib.SMTPException("rechazado")), \
         pytest.raises(smtplib.SMTPException):
        auth.enviar_email_contacto("Vero", "vero@ejemplo.com", "Hola")
