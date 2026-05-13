from datetime import datetime, timezone
from unittest.mock import patch

from backend.app.models import Usuario
from backend.app.auth import hashear_password

USUARIO_VALIDO = {"email": "test@example.com", "password": "Segura1234"}


def _crear_verificado(db, email, password, rol="registrado"):
    u = Usuario(email=email, password=hashear_password(password), rol=rol,
                activo=1, email_verificado=1, created_at=datetime.now(timezone.utc))
    db.add(u); db.commit(); db.refresh(u)
    return u


# ── Registro ────────────────────────────────────────────────────────────────

def test_registro_exitoso(client):
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        response = client.post("/auth/registro", json=USUARIO_VALIDO)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == USUARIO_VALIDO["email"]
    assert data["rol"] == "registrado"
    assert data["email_verificado"] is False


def test_registro_email_duplicado(client):
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO_VALIDO)
        response = client.post("/auth/registro", json=USUARIO_VALIDO)
    assert response.status_code == 400


def test_registro_contrasena_debil(client):
    response = client.post("/auth/registro", json={"email": "otro@example.com", "password": "debil"})
    assert response.status_code == 422


def test_registro_honeypot_silencioso(client):
    # Si el campo trampa llega relleno, se devuelve 201 sin crear cuenta
    response = client.post("/auth/registro", json={**USUARIO_VALIDO, "sitio_web": "http://spam.example.com"})
    assert response.status_code == 201
    # El usuario no debe existir en la BD (la cuenta no se creó)
    response2 = client.post("/auth/login", json=USUARIO_VALIDO)
    assert response2.status_code == 401


# ── Login ────────────────────────────────────────────────────────────────────

def test_login_exitoso(client, db):
    _crear_verificado(db, USUARIO_VALIDO["email"], USUARIO_VALIDO["password"])
    response = client.post("/auth/login", json=USUARIO_VALIDO)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_email_no_verificado(client):
    # Usuario registrado pero que no ha verificado el email
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO_VALIDO)
    response = client.post("/auth/login", json=USUARIO_VALIDO)
    assert response.status_code == 403


def test_login_contrasena_incorrecta(client, db):
    _crear_verificado(db, USUARIO_VALIDO["email"], USUARIO_VALIDO["password"])
    response = client.post("/auth/login", json={"email": USUARIO_VALIDO["email"], "password": "Incorrecta99"})
    assert response.status_code == 401


def test_login_email_inexistente(client):
    response = client.post("/auth/login", json={"email": "noexiste@example.com", "password": "Cualquiera1"})
    assert response.status_code == 401


# ── Zona privada ─────────────────────────────────────────────────────────────

def _obtener_token(client, db):
    _crear_verificado(db, USUARIO_VALIDO["email"], USUARIO_VALIDO["password"])
    r = client.post("/auth/login", json=USUARIO_VALIDO)
    return r.json()["access_token"]


def test_perfil_sin_token(client):
    response = client.get("/privado/perfil")
    assert response.status_code == 401


def test_perfil_con_token(client, db):
    token = _obtener_token(client, db)
    response = client.get("/privado/perfil", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == USUARIO_VALIDO["email"]


def test_resumen_sin_token(client):
    response = client.get("/privado/resumen-exclusivo")
    assert response.status_code == 401


def test_resumen_con_token(client, db):
    token = _obtener_token(client, db)
    response = client.get("/privado/resumen-exclusivo", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "contenido" in response.json()


def test_resumen_tabla_con_token(client, db):
    token = _obtener_token(client, db)
    response = client.get("/privado/resumen-tabla", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "filas" in data
    assert "total_global" in data
    assert "importe_global" in data


def test_resumen_tabla_sin_token(client):
    response = client.get("/privado/resumen-tabla")
    assert response.status_code == 401
