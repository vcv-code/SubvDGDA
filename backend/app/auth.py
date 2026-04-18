import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTOS = 60


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
