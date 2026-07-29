"""
Tests de verificación de email — /auth/verificar

Cubre:
  - Login bloqueado mientras la cuenta no está verificada
  - GET /auth/verificar con token válido verifica la cuenta
  - Login funciona tras verificar
  - GET /auth/verificar con token inválido devuelve 400
  - GET /auth/verificar con token ya usado devuelve 400
  - GET /auth/verificar con token expirado devuelve 400
  - /auth/reset también activa email_verificado

Que el alta genere la cuenta sin verificar y dispare el email se prueba en
test_admin.py, contra POST /admin/usuarios: desde que se retiró el registro
público, esa es la única vía de creación de cuentas.
"""

from datetime import datetime, timedelta, timezone

from backend.app.auth import crear_verificacion_token, verificacion_expira_en
from backend.app.models import VerificacionToken, Usuario, ResetToken

USUARIO = {"email": "verif@example.com", "password": "Segura1234"}


def _sembrar_sin_verificar(db, crear_usuario):
    """Cuenta pendiente de verificar, con su token, tal y como la deja el alta.

    Se siembra en BD en vez de llamar al endpoint de alta para no arrastrar
    aquí un admin autenticado: estos tests van del flujo de verificación, no
    de quién crea la cuenta.
    """
    usuario = crear_usuario(USUARIO["email"], USUARIO["password"], email_verificado=0)
    token = crear_verificacion_token()
    db.add(VerificacionToken(
        id_usuario=usuario.id_usuario,
        token=token,
        expira_en=verificacion_expira_en(),
    ))
    db.commit()
    return usuario, token


# ── Login sin verificar ───────────────────────────────────────────────────────

def test_login_bloqueado_sin_verificar(client, db, crear_usuario):
    _sembrar_sin_verificar(db, crear_usuario)
    r = client.post("/auth/login", json=USUARIO)
    assert r.status_code == 403


# ── GET /auth/verificar ───────────────────────────────────────────────────────

def test_verificar_token_valido_activa_cuenta(client, db, crear_usuario):
    usuario, token = _sembrar_sin_verificar(db, crear_usuario)

    r = client.get(f"/auth/verificar?token={token}")
    assert r.status_code == 200
    assert "mensaje" in r.json()

    db.refresh(usuario)
    assert usuario.email_verificado == 1


def test_login_exitoso_tras_verificar(client, db, crear_usuario):
    _, token = _sembrar_sin_verificar(db, crear_usuario)

    client.get(f"/auth/verificar?token={token}")
    r = client.post("/auth/login", json=USUARIO)
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_verificar_token_invalido_devuelve_400(client):
    r = client.get("/auth/verificar?token=" + "a" * 64)
    assert r.status_code == 400


def test_verificar_token_ya_usado_devuelve_400(client, db, crear_usuario):
    _, token = _sembrar_sin_verificar(db, crear_usuario)

    client.get(f"/auth/verificar?token={token}")
    r = client.get(f"/auth/verificar?token={token}")
    assert r.status_code == 400


def test_verificar_token_expirado_devuelve_400(client, db, crear_usuario):
    usuario, _ = _sembrar_sin_verificar(db, crear_usuario)
    token_expirado = "b" * 64
    db.add(VerificacionToken(
        id_usuario=usuario.id_usuario,
        token=token_expirado,
        expira_en=datetime.now(timezone.utc) - timedelta(hours=1),
    ))
    db.commit()

    r = client.get(f"/auth/verificar?token={token_expirado}")
    assert r.status_code == 400


# ── Reset también verifica ────────────────────────────────────────────────────

def test_reset_activa_email_verificado(client, db, crear_usuario):
    usuario, _ = _sembrar_sin_verificar(db, crear_usuario)
    assert usuario.email_verificado == 0

    reset_tok = "c" * 64
    db.add(ResetToken(
        id_usuario=usuario.id_usuario,
        token=reset_tok,
        expira_en=datetime.now(timezone.utc) + timedelta(minutes=15),
    ))
    db.commit()

    client.post("/auth/reset", json={"token": reset_tok, "contrasena_nueva": "NuevaClave99"})
    db.refresh(usuario)
    assert usuario.email_verificado == 1
