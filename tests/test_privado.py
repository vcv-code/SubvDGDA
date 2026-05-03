USUARIO = {"email": "test@example.com", "password": "Segura1234"}
NUEVA_PASS = "NuevaPass99"


def _token(client):
    client.post("/auth/registro", json=USUARIO)
    r = client.post("/auth/login", json=USUARIO)
    return r.json()["access_token"]


def _headers(client):
    return {"Authorization": f"Bearer {_token(client)}"}


# ── Cambiar contraseña ────────────────────────────────────────────────────────

def test_cambiar_password_correcto(client):
    headers = _headers(client)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_cambiar_password_actual_incorrecta(client):
    headers = _headers(client)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": "Incorrecta99", "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    assert r.status_code == 401


def test_cambiar_password_nueva_debil(client):
    headers = _headers(client)
    r = client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": "debil"},
        headers=headers,
    )
    assert r.status_code == 422


def test_cambiar_password_nuevo_login_funciona(client):
    headers = _headers(client)
    client.put(
        "/privado/cambiar-contrasena",
        json={"contrasena_actual": USUARIO["password"], "contrasena_nueva": NUEVA_PASS},
        headers=headers,
    )
    r = client.post("/auth/login", json={"email": USUARIO["email"], "password": NUEVA_PASS})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_cambiar_password_viejo_login_falla(client):
    headers = _headers(client)
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
