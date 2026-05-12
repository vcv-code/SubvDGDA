from datetime import datetime, timezone
from backend.app.models import Usuario
from backend.app.auth import hashear_password

USUARIO = {"email": "test@example.com", "password": "Segura1234"}
NUEVA_PASS = "NuevaPass99"


def _crear_verificado(db, email, password):
    u = Usuario(email=email, password=hashear_password(password), rol="registrado",
                activo=1, email_verificado=1, created_at=datetime.now(timezone.utc))
    db.add(u); db.commit(); db.refresh(u)
    return u


def _token(client, db):
    _crear_verificado(db, USUARIO["email"], USUARIO["password"])
    r = client.post("/auth/login", json=USUARIO)
    return r.json()["access_token"]


def _headers(client, db):
    return {"Authorization": f"Bearer {_token(client, db)}"}


# ── Cambiar contraseña ────────────────────────────────────────────────────────

def test_cambiar_password_correcto(client, db):
    headers = _headers(client, db)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_cambiar_password_actual_incorrecta(client, db):
    headers = _headers(client, db)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": "Incorrecta99", "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    assert r.status_code == 401


def test_cambiar_password_nueva_debil(client, db):
    headers = _headers(client, db)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": "debil"},
        headers=headers,
    )
    assert r.status_code == 422


def test_cambiar_password_nuevo_login_funciona(client, db):
    headers = _headers(client, db)
    client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    r = client.post("/auth/login", json={"email": USUARIO["email"], "password": NUEVA_PASS})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_cambiar_password_viejo_login_falla(client, db):
    headers = _headers(client, db)
    client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    r = client.post("/auth/login", json=USUARIO)
    assert r.status_code == 401


def test_cambiar_password_sin_token(client):
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
    )
    assert r.status_code == 401
