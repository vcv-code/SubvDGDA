from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app.models import ResetToken

USUARIO = {"email": "recuperar@example.com", "password": "Segura1234"}


def _sembrar(crear_usuario):
    """Cuenta pendiente de verificar, como la deja el alta desde el panel admin.

    Se siembra en BD porque estos tests van del flujo de recuperación, no de
    quién crea la cuenta: montar aquí un admin autenticado solo para sembrar
    añadiría ruido sin cubrir nada nuevo.
    """
    return crear_usuario(USUARIO["email"], USUARIO["password"], email_verificado=0)


# ──────────────────────────────────────────────
# /auth/recuperar
# ──────────────────────────────────────────────

def test_recuperar_email_existente_devuelve_200(client, crear_usuario):
    _sembrar(crear_usuario)
    with patch("backend.app.routers.auth.enviar_email_recuperacion"):
        r = client.post("/auth/recuperar", json={"email": USUARIO["email"]})
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_recuperar_email_inexistente_devuelve_igual(client):
    # No revelamos si el email existe o no — misma respuesta
    with patch("backend.app.routers.auth.enviar_email_recuperacion"):
        r = client.post("/auth/recuperar", json={"email": "noexiste@example.com"})
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_recuperar_crea_token_en_bd(client, db, crear_usuario):
    _sembrar(crear_usuario)
    with patch("backend.app.routers.auth.enviar_email_recuperacion"):
        client.post("/auth/recuperar", json={"email": USUARIO["email"]})
    assert db.query(ResetToken).count() == 1


def test_recuperar_envia_email(client, crear_usuario):
    _sembrar(crear_usuario)
    with patch("backend.app.routers.auth.enviar_email_recuperacion") as mock_enviar:
        client.post("/auth/recuperar", json={"email": USUARIO["email"]})
    mock_enviar.assert_called_once_with(USUARIO["email"], mock_enviar.call_args[0][1])


# ──────────────────────────────────────────────
# /auth/reset
# ──────────────────────────────────────────────

def test_reset_token_valido_cambia_password(client, db, crear_usuario):
    _sembrar(crear_usuario)
    with patch("backend.app.routers.auth.enviar_email_recuperacion"):
        client.post("/auth/recuperar", json={"email": USUARIO["email"]})
    token = db.query(ResetToken).first().token

    r = client.post("/auth/reset", json={"token": token, "contrasena_nueva": "NuevaClave99"})
    assert r.status_code == 200

    # Verificamos que el login funciona con la nueva contraseña
    login = client.post("/auth/login", json={"email": USUARIO["email"], "password": "NuevaClave99"})
    assert login.status_code == 200


def test_reset_token_invalido_devuelve_400(client):
    r = client.post("/auth/reset", json={"token": "tokenfalso" * 6, "contrasena_nueva": "NuevaClave99"})
    assert r.status_code == 400


def test_reset_token_ya_usado_devuelve_400(client, db, crear_usuario):
    _sembrar(crear_usuario)
    with patch("backend.app.routers.auth.enviar_email_recuperacion"):
        client.post("/auth/recuperar", json={"email": USUARIO["email"]})
    token = db.query(ResetToken).first().token

    # Primer uso — correcto
    client.post("/auth/reset", json={"token": token, "contrasena_nueva": "NuevaClave99"})
    # Segundo uso — debe fallar
    r = client.post("/auth/reset", json={"token": token, "contrasena_nueva": "OtraClave99"})
    assert r.status_code == 400


def test_reset_token_expirado_devuelve_400(client, db, crear_usuario):
    usuario = _sembrar(crear_usuario)
    # Insertamos un token con fecha de expiración en el pasado
    token_expirado = "a" * 64
    db.add(ResetToken(
        id_usuario=usuario.id_usuario,
        token=token_expirado,
        expira_en=datetime.now(timezone.utc) - timedelta(minutes=1),
    ))
    db.commit()

    r = client.post("/auth/reset", json={"token": token_expirado, "contrasena_nueva": "NuevaClave99"})
    assert r.status_code == 400


def test_reset_password_debil_devuelve_422(client):
    r = client.post("/auth/reset", json={"token": "cualquiertoken", "contrasena_nueva": "debil"})
    assert r.status_code == 422
