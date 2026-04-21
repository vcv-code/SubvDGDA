import pytest

USUARIO_VALIDO = {"email": "test@example.com", "password": "Segura1234"}


# ── Registro ────────────────────────────────────────────────────────────────

def test_registro_exitoso(client):
    response = client.post("/auth/registro", json=USUARIO_VALIDO)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == USUARIO_VALIDO["email"]
    assert data["rol"] == "registrado"


def test_registro_email_duplicado(client):
    client.post("/auth/registro", json=USUARIO_VALIDO)
    response = client.post("/auth/registro", json=USUARIO_VALIDO)
    assert response.status_code == 400


def test_registro_contrasena_debil(client):
    # Sin mayúscula, sin número: debe rechazarse con 422
    response = client.post("/auth/registro", json={"email": "otro@example.com", "password": "debil"})
    assert response.status_code == 422


# ── Login ────────────────────────────────────────────────────────────────────

def test_login_exitoso(client):
    client.post("/auth/registro", json=USUARIO_VALIDO)
    response = client.post("/auth/login", json=USUARIO_VALIDO)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_contrasena_incorrecta(client):
    client.post("/auth/registro", json=USUARIO_VALIDO)
    response = client.post("/auth/login", json={"email": USUARIO_VALIDO["email"], "password": "Incorrecta99"})
    assert response.status_code == 401


def test_login_email_inexistente(client):
    response = client.post("/auth/login", json={"email": "noexiste@example.com", "password": "Cualquiera1"})
    assert response.status_code == 401


# ── Zona privada ─────────────────────────────────────────────────────────────

def _obtener_token(client):
    client.post("/auth/registro", json=USUARIO_VALIDO)
    r = client.post("/auth/login", json=USUARIO_VALIDO)
    return r.json()["access_token"]


def test_perfil_sin_token(client):
    response = client.get("/privado/perfil")
    assert response.status_code == 401


def test_perfil_con_token(client):
    token = _obtener_token(client)
    response = client.get("/privado/perfil", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == USUARIO_VALIDO["email"]


def test_resumen_sin_token(client):
    response = client.get("/privado/resumen-exclusivo")
    assert response.status_code == 401


def test_resumen_con_token(client):
    token = _obtener_token(client)
    response = client.get("/privado/resumen-exclusivo", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "contenido" in response.json()
