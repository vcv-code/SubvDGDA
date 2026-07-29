from datetime import datetime, timezone

from backend.app.models import Usuario
from backend.app.auth import hashear_password

USUARIO_VALIDO = {"email": "test@example.com", "password": "Segura1234"}


def _crear_verificado(db, email, password, rol="registrado"):
    u = Usuario(email=email, password=hashear_password(password), rol=rol,
                activo=1, email_verificado=1, created_at=datetime.now(timezone.utc))
    db.add(u); db.commit(); db.refresh(u)
    return u


# El alta de usuarios ya no vive aquí: se retiró el registro público y la
# creación de cuentas pasó a POST /admin/usuarios, probado en test_admin.py.
# Con el endpoint público desapareció también su honeypot, que solo tenía
# sentido frente a un formulario abierto a cualquiera.


# ── Login ────────────────────────────────────────────────────────────────────

def test_login_exitoso(client, db):
    _crear_verificado(db, USUARIO_VALIDO["email"], USUARIO_VALIDO["password"])
    response = client.post("/auth/login", json=USUARIO_VALIDO)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_email_no_verificado(client, db):
    # Cuenta creada pero cuyo titular no ha confirmado aún su dirección
    _crear_verificado(db, USUARIO_VALIDO["email"], USUARIO_VALIDO["password"])
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO_VALIDO["email"]).first()
    usuario.email_verificado = 0
    db.commit()

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
