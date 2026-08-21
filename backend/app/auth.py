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

# ── Correo saliente ───────────────────────────────────────────────────────────
# Los valores por defecto son los de desarrollo (Mailpit): sin autenticación,
# sin cifrado y con un dominio ficticio. En producción se sobrescriben por
# variables de entorno; ver docker/.env.example.
#
# Se usa `or` en vez del segundo argumento de getenv porque docker compose
# propaga las variables no definidas como cadena vacía, no como ausentes: con
# `getenv(x, defecto)` una variable vacía en .env dejaría el valor en "".
SMTP_HOST     = os.getenv("SMTP_HOST") or "localhost"
SMTP_PORT     = int(os.getenv("SMTP_PORT") or 1025)
SMTP_USER     = os.getenv("SMTP_USER") or ""
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or ""
SMTP_TLS      = (os.getenv("SMTP_TLS") or "").strip().lower() in ("1", "true", "yes", "si", "sí")
# Sin timeout, un servidor SMTP que acepta la conexión y no responde dejaría la
# petición colgada indefinidamente.
SMTP_TIMEOUT  = 15

EMAIL_FROM = os.getenv("EMAIL_FROM") or "noreply@subvencionesDGDA.local"
# Buzón que recibe los mensajes del formulario de contacto. En producción se
# configura con la dirección real vía env var; en dev cae en Mailpit como el resto.
EMAIL_CONTACTO = os.getenv("EMAIL_CONTACTO") or EMAIL_FROM

# Pie de los correos salientes.
#
# No es un adorno: el dominio suena semioficial y quien recibe un correo de
# «Subvenciones DGDA» puede creer que se lo manda la administración que
# concede las ayudas. Aquí es donde se corta esa confusión, porque lo lee
# quien ya tiene el mensaje delante. La dirección de envío y el nombre visible
# de la cuenta ayudan, pero llegan a menos gente que esto.
FIRMA_EMAIL = (
    "—\n"
    "Subvenciones DGDA · {sitio}\n"
    "Web independiente de análisis de datos públicos. No es un sitio oficial\n"
    "ni tramita subvenciones: los datos proceden del BDNS y del BOE.\n"
)


def _firma() -> str:
    """El pie, con la dirección real del sitio en cada entorno."""
    return FIRMA_EMAIL.format(sitio=SITE_URL.replace("https://", "").replace("http://", ""))

# Base de los enlaces que viajan dentro de los correos (verificación y
# recuperación). Sin barra final, para no componer rutas con doble barra.
SITE_URL = (os.getenv("SITE_URL") or "https://subvencionesDGDA.local").rstrip("/")


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


def _entregar_mensaje(msg: EmailMessage) -> None:
    """Entrega un mensaje al servidor SMTP configurado.

    Con los valores por defecto (Mailpit) se conecta en claro y envía sin más,
    igual que antes. `SMTP_TLS` y `SMTP_USER` solo entran en juego si se
    configuran, que es lo que exigen los proveedores reales como Gmail o Brevo.
    """
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as servidor:
        if SMTP_TLS:
            servidor.starttls()
        if SMTP_USER:
            servidor.login(SMTP_USER, SMTP_PASSWORD)
        servidor.send_message(msg)


def enviar_email_verificacion(email_destino: str, token: str) -> None:
    enlace = f"{SITE_URL}/verificar-email.html?token={token}"

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
        f"{_firma()}"
    )

    # OSError cubre conexión rechazada y timeout, que no son SMTPException y
    # dejarían la petición en error 500 en vez de seguir adelante.
    try:
        _entregar_mensaje(msg)
    except (smtplib.SMTPException, OSError) as e:
        logger.error("Error enviando email de verificación a %s: %s", email_destino, e)


def enviar_email_recuperacion(email_destino: str, token: str) -> None:
    """Envía el email con el enlace de recuperación al servidor SMTP (Mailpit en dev)."""
    enlace = f"{SITE_URL}/reset-password.html?token={token}"

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
        f"{_firma()}"
    )

    try:
        _entregar_mensaje(msg)
    except (smtplib.SMTPException, OSError) as e:
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
        f"Mensaje:\n{mensaje}\n\n"
        f"—\nEnviado desde el formulario de {SITE_URL}\n"
    )

    _entregar_mensaje(msg)
