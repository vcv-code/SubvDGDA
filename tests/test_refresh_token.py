USUARIO = {"email": "test@example.com", "password": "Segura1234"}


def _login(client):
    client.post("/auth/registro", json=USUARIO)
    return client.post("/auth/login", json=USUARIO).json()


def test_login_devuelve_refresh_token(client):
    data = _login(client)
    assert "refresh_token" in data
    assert len(data["refresh_token"]) == 64


def test_refresh_devuelve_nuevo_access_token(client):
    data = _login(client)
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_rota_el_token(client):
    data = _login(client)
    nuevo = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]}).json()
    # El token original ya no sirve (rotación)
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 401
    # Pero el nuevo sí
    r2 = client.post("/auth/refresh", json={"refresh_token": nuevo["refresh_token"]})
    assert r2.status_code == 200


def test_refresh_token_invalido(client):
    _login(client)
    r = client.post("/auth/refresh", json={"refresh_token": "tokenfalso" * 6})
    assert r.status_code == 401


def test_logout_revoca_token(client):
    data = _login(client)
    client.post("/auth/logout", json={"refresh_token": data["refresh_token"]})
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 401


def test_logout_token_inexistente_no_falla(client):
    _login(client)
    r = client.post("/auth/logout", json={"refresh_token": "noexiste" * 8})
    assert r.status_code == 200


def test_cambiar_password_revoca_refresh_tokens(client):
    data = _login(client)
    refresh_token = data["refresh_token"]
    token = data["access_token"]

    client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": "NuevaPass99"},
        headers={"Authorization": f"Bearer {token}"},
    )

    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401
