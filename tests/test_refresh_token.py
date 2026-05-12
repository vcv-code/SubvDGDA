from datetime import datetime, timezone
from backend.app.models import Usuario
from backend.app.auth import hashear_password

USUARIO = {"email": "test@example.com", "password": "Segura1234"}


def _crear_verificado(db, email, password):
    u = Usuario(email=email, password=hashear_password(password), rol="registrado",
                activo=1, email_verificado=1, created_at=datetime.now(timezone.utc))
    db.add(u); db.commit(); db.refresh(u)
    return u


def _login(client, db):
    _crear_verificado(db, USUARIO["email"], USUARIO["password"])
    return client.post("/auth/login", json=USUARIO).json()


def test_login_devuelve_refresh_token(client, db):
    data = _login(client, db)
    assert "refresh_token" in data
    assert len(data["refresh_token"]) == 64


def test_refresh_devuelve_nuevo_access_token(client, db):
    data = _login(client, db)
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_rota_el_token(client, db):
    data = _login(client, db)
    nuevo = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]}).json()
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 401
    r2 = client.post("/auth/refresh", json={"refresh_token": nuevo["refresh_token"]})
    assert r2.status_code == 200


def test_refresh_token_invalido(client, db):
    _login(client, db)
    r = client.post("/auth/refresh", json={"refresh_token": "tokenfalso" * 6})
    assert r.status_code == 401


def test_logout_revoca_token(client, db):
    data = _login(client, db)
    client.post("/auth/logout", json={"refresh_token": data["refresh_token"]})
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 401


def test_logout_token_inexistente_no_falla(client, db):
    _login(client, db)
    r = client.post("/auth/logout", json={"refresh_token": "noexiste" * 8})
    assert r.status_code == 200


def test_cambiar_password_revoca_refresh_tokens(client, db):
    data = _login(client, db)
    refresh_token = data["refresh_token"]
    token = data["access_token"]

    client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": "NuevaPass99"},
        headers={"Authorization": f"Bearer {token}"},
    )

    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401
