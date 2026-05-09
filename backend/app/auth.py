import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import bcrypt
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTOS   = 60
REFRESH_EXPIRE_DIAS    = 30
RESET_EXPIRE_MINUTOS   = 15

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
EMAIL_FROM = "noreply@subvencionesDGDA.local"


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


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

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.send_message(msg)
