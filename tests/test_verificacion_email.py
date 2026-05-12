"""
Tests de verificación de email — /auth/verificar

Cubre:
  - Registro crea usuario con email_verificado=False y genera token
  - Registro envía el email de verificación
  - GET /auth/verificar con token válido verifica la cuenta
  - Login funciona tras verificar
  - GET /auth/verificar con token inválido devuelve 400
  - GET /auth/verificar con token ya usado devuelve 400
  - GET /auth/verificar con token expirado devuelve 400
  - /auth/reset también activa email_verificado
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app.models import VerificacionToken, Usuario, ResetToken

USUARIO = {"email": "verif@example.com", "password": "Segura1234"}


def _registrar(client):
    """Registra usuario mockeando el envío de email. Devuelve el mock para inspección."""
    with patch("backend.app.routers.auth.enviar_email_verificacion") as mock_enviar:
        client.post("/auth/registro", json=USUARIO)
    return mock_enviar


# ── Registro ──────────────────────────────────────────────────────────────────

def test_registro_crea_usuario_no_verificado(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
    assert usuario is not None
    assert usuario.email_verificado == 0


def test_registro_crea_token_verificacion_en_bd(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
    token = db.query(VerificacionToken).filter(VerificacionToken.id_usuario == usuario.id_usuario).first()
    assert token is not None
    assert token.usado is False


def test_registro_envia_email_verificacion(client):
    mock_enviar = _registrar(client)
    mock_enviar.assert_called_once_with(USUARIO["email"], mock_enviar.call_args[0][1])


def test_login_bloqueado_sin_verificar(client):
    _registrar(client)
    r = client.post("/auth/login", json=USUARIO)
    assert r.status_code == 403


# ── GET /auth/verificar ───────────────────────────────────────────────────────

def test_verificar_token_valido_activa_cuenta(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
    token = db.query(VerificacionToken).filter(VerificacionToken.id_usuario == usuario.id_usuario).first().token

    r = client.get(f"/auth/verificar?token={token}")
    assert r.status_code == 200
    assert "mensaje" in r.json()

    db.refresh(usuario)
    assert usuario.email_verificado == 1


def test_login_exitoso_tras_verificar(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
    token = db.query(VerificacionToken).filter(VerificacionToken.id_usuario == usuario.id_usuario).first().token

    client.get(f"/auth/verificar?token={token}")
    r = client.post("/auth/login", json=USUARIO)
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_verificar_token_invalido_devuelve_400(client):
    r = client.get("/auth/verificar?token=" + "a" * 64)
    assert r.status_code == 400


def test_verificar_token_ya_usado_devuelve_400(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
    token = db.query(VerificacionToken).filter(VerificacionToken.id_usuario == usuario.id_usuario).first().token

    client.get(f"/auth/verificar?token={token}")
    r = client.get(f"/auth/verificar?token={token}")
    assert r.status_code == 400


def test_verificar_token_expirado_devuelve_400(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
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

def test_reset_activa_email_verificado(client, db):
    _registrar(client)
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO["email"]).first()
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
