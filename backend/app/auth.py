import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

logger = logging.getLogger(__name__)

import bcrypt
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTOS      = 15
REFRESH_EXPIRE_DIAS       = 30
RESET_EXPIRE_MINUTOS      = 15
VERIFICACION_EXPIRE_HORAS = 24

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
EMAIL_FROM = "noreply@subvencionesDGDA.local"
# Buzón que recibe los mensajes del formulario de contacto. En producción se
# configura con la dirección real vía env var; en dev cae en Mailpit como el resto.
EMAIL_CONTACTO = os.getenv("EMAIL_CONTACTO", EMAIL_FROM)


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verificar_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def crear_token(email: str, rol: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTOS)
    payload = {"sub": email, "rol": rol, "exp": expira}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Devuelve el payload del token o lanza JWTError si es inválido o ha expirado."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def crear_refresh_token() -> str:
    """Genera un token opaco de 64 caracteres hexadecimales."""
    return secrets.token_hex(32)


def refresh_expira_en() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DIAS)


def crear_reset_token() -> str:
    """Genera un token opaco de 64 caracteres hexadecimales."""
    return secrets.token_hex(32)


def reset_expira_en() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=RESET_EXPIRE_MINUTOS)


def crear_verificacion_token() -> str:
    return secrets.token_hex(32)


def verificacion_expira_en() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=VERIFICACION_EXPIRE_HORAS)


def enviar_email_verificacion(email_destino: str, token: str) -> None:
    enlace = f"https://subvencionesDGDA.local/verificar-email.html?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verifica tu correo — Subvenciones DGDA"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = email_destino
    msg.set_content(
        f"Hola,\n\n"
        f"Gracias por registrarte. Haz clic en el siguiente enlace para verificar tu dirección de correo:\n\n"
        f"{enlace}\n\n"
        f"El enlace caduca en {VERIFICACION_EXPIRE_HORAS} horas y solo puede usarse una vez.\n\n"
        f"Si no has creado una cuenta, ignora este mensaje.\n\n"
        f"Subvenciones DGDA"
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.send_message(msg)
    except smtplib.SMTPException as e:
        logger.error("Error enviando email de verificación a %s: %s", email_destino, e)


def enviar_email_recuperacion(email_destino: str, token: str) -> None:
    """Envía el email con el enlace de recuperación al servidor SMTP (Mailpit en dev)."""
    enlace = f"https://subvencionesDGDA.local/reset-password.html?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Recuperación de contraseña — Subvenciones DGDA"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = email_destino
    msg.set_content(
        f"Hola,\n\n"
        f"Has solicitado recuperar tu contraseña. Usa el siguiente enlace:\n\n"
        f"{enlace}\n\n"
        f"El enlace caduca en {RESET_EXPIRE_MINUTOS} minutos y solo puede usarse una vez.\n\n"
        f"Si no has solicitado este cambio, ignora este mensaje.\n\n"
        f"Subvenciones DGDA"
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.send_message(msg)
    except smtplib.SMTPException as e:
        logger.error("Error enviando email de recuperación a %s: %s", email_destino, e)


def enviar_email_contacto(nombre: str, email_remitente: str, mensaje: str) -> None:
    """Reenvía un mensaje del formulario de contacto al buzón de soporte.

    A diferencia de los otros envíos (fire-and-forget), aquí propagamos el
    error si el SMTP falla, para que el endpoint pueda avisar a la persona de
    que su mensaje NO se ha enviado en vez de fingir éxito.
    """
    msg = EmailMessage()
    msg["Subject"]  = f"Contacto web — {nombre or email_remitente}"
    msg["From"]     = EMAIL_FROM
    msg["To"]       = EMAIL_CONTACTO
    msg["Reply-To"] = email_remitente  # responder va directo a quien escribió
    msg.set_content(
        f"Nuevo mensaje desde el formulario de contacto:\n\n"
        f"Nombre: {nombre or '(no indicado)'}\n"
        f"Email:  {email_remitente}\n\n"
        f"Mensaje:\n{mensaje}\n"
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.send_message(msg)
