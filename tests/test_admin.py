"""
Tests del panel de administración — /admin/*

Cubre:
  - Acceso denegado sin token (401) y con rol insuficiente (403)
  - GET /admin/estado
  - GET /admin/usuarios
  - PATCH /admin/usuarios/{id}/rol
  - PATCH /admin/usuarios/{id}/activo
  - DELETE /admin/usuarios/{id}
  - GET /admin/avisos y GET /admin/avisos?incluir_resueltas=true
  - PATCH /admin/avisos/{id}/desactivar
  - PATCH /admin/avisos/{id}/reactivar
  - DELETE /admin/avisos/{id}
  - GET /admin/logs
"""

from datetime import datetime, date, timedelta, timezone
from unittest.mock import patch

from backend.app.models import Convocatoria, Solicitud, Usuario
from backend.app.auth import hashear_password

ADMIN    = {"email": "admin@test.com",      "password": "Admin1234"}
USUARIO  = {"email": "usuario@test.com",    "password": "Usuario1234"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _registrar_admin(db):
    """Crea un usuario con rol admin directamente en BD."""
    admin = Usuario(
        email=ADMIN["email"],
        password=hashear_password(ADMIN["password"]),
        rol="admin",
        activo=1,
        email_verificado=1,
        created_at=datetime.now(timezone.utc),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _token_admin(client, db):
    _registrar_admin(db)
    r = client.post("/auth/login", json=ADMIN)
    return r.json()["access_token"]


def _token_registrado(client, db):
    u = Usuario(email=USUARIO["email"], password=hashear_password(USUARIO["password"]),
                rol="registrado", activo=1, email_verificado=1, created_at=datetime.now(timezone.utc))
    db.add(u); db.commit()
    r = client.post("/auth/login", json=USUARIO)
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _convocatoria(db, **kwargs):
    defaults = dict(
        num_convoc="TEST-2025",
        titulo_convoc="Convocatoria de prueba",
        tipo_convoc="epa",
        anio_convocatoria=2025,
        fecha_convocatoria=None,
        fecha_resolucion=None,
    )
    defaults.update(kwargs)
    c = Convocatoria(**defaults)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ── Acceso ────────────────────────────────────────────────────────────────────

def test_estado_sin_token_devuelve_401(client):
    r = client.get("/admin/estado")
    assert r.status_code == 401


def test_estado_rol_registrado_devuelve_403(client, db):
    token = _token_registrado(client, db)
    r = client.get("/admin/estado", headers=_headers(token))
    assert r.status_code == 403


def test_estado_rol_admin_devuelve_200(client, db):
    token = _token_admin(client, db)
    r = client.get("/admin/estado", headers=_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert data["health"] == "ok"
    assert "total_usuarios" in data
    assert "total_convocatorias" in data
    assert "total_solicitudes" in data


# ── Usuarios ──────────────────────────────────────────────────────────────────

def test_listar_usuarios(client, db):
    token = _token_admin(client, db)
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO)
    r = client.get("/admin/usuarios", headers=_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert "usuarios" in data and "total" in data
    assert data["total"] == 2
    emails = [u["email"] for u in data["usuarios"]]
    assert ADMIN["email"] in emails
    assert USUARIO["email"] in emails


def test_cambiar_rol_a_admin(client, db):
    token = _token_admin(client, db)
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_usr = next(u["id_usuario"] for u in usuarios if u["email"] == USUARIO["email"])

    r = client.patch(
        f"/admin/usuarios/{id_usr}/rol",
        json={"rol": "admin"},
        headers=_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["rol"] == "admin"


def test_cambiar_propio_rol_devuelve_400(client, db):
    token = _token_admin(client, db)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_admin = next(u["id_usuario"] for u in usuarios if u["email"] == ADMIN["email"])

    r = client.patch(
        f"/admin/usuarios/{id_admin}/rol",
        json={"rol": "registrado"},
        headers=_headers(token),
    )
    assert r.status_code == 400


def test_desactivar_usuario(client, db):
    token = _token_admin(client, db)
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_usr = next(u["id_usuario"] for u in usuarios if u["email"] == USUARIO["email"])

    r = client.patch(
        f"/admin/usuarios/{id_usr}/activo",
        json={"activo": False},
        headers=_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["activo"] is False


def test_desactivar_propia_cuenta_devuelve_400(client, db):
    token = _token_admin(client, db)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_admin = next(u["id_usuario"] for u in usuarios if u["email"] == ADMIN["email"])

    r = client.patch(
        f"/admin/usuarios/{id_admin}/activo",
        json={"activo": False},
        headers=_headers(token),
    )
    assert r.status_code == 400


def test_usuario_inexistente_devuelve_404(client, db):
    token = _token_admin(client, db)
    r = client.patch("/admin/usuarios/9999/rol", json={"rol": "admin"}, headers=_headers(token))
    assert r.status_code == 404


def test_eliminar_usuario(client, db):
    token = _token_admin(client, db)
    with patch("backend.app.routers.auth.enviar_email_verificacion"):
        client.post("/auth/registro", json=USUARIO)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_usr = next(u["id_usuario"] for u in usuarios if u["email"] == USUARIO["email"])

    r = client.delete(f"/admin/usuarios/{id_usr}", headers=_headers(token))
    assert r.status_code == 200

    usuarios_tras = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    assert not any(u["id_usuario"] == id_usr for u in usuarios_tras)


def test_eliminar_propia_cuenta_devuelve_400(client, db):
    token = _token_admin(client, db)
    usuarios = client.get("/admin/usuarios", headers=_headers(token)).json()["usuarios"]
    id_admin = next(u["id_usuario"] for u in usuarios if u["email"] == ADMIN["email"])

    r = client.delete(f"/admin/usuarios/{id_admin}", headers=_headers(token))
    assert r.status_code == 400


def test_eliminar_usuario_inexistente_devuelve_404(client, db):
    token = _token_admin(client, db)
    r = client.delete("/admin/usuarios/9999", headers=_headers(token))
    assert r.status_code == 404


def test_listar_usuarios_paginacion(client, db):
    token = _token_admin(client, db)
    # 5 registrados + el admin = 6 usuarios en total
    for i in range(5):
        db.add(Usuario(email=f"u{i}@test.com", password=hashear_password("Usuario1234"),
                       rol="registrado", activo=1, email_verificado=1,
                       created_at=datetime.now(timezone.utc)))
    db.commit()

    p1 = client.get("/admin/usuarios?pagina=1&limite=2", headers=_headers(token)).json()
    assert p1["total"] == 6
    assert len(p1["usuarios"]) == 2

    # Página fuera de rango: lista vacía pero total correcto
    p99 = client.get("/admin/usuarios?pagina=99&limite=2", headers=_headers(token)).json()
    assert p99["usuarios"] == []
    assert p99["total"] == 6


# ── Logs del cron ─────────────────────────────────────────────────────────────

def test_logs_cron_requiere_admin(client):
    assert client.get("/admin/logs/cron?fichero=bdns").status_code == 401


def test_logs_cron_fichero_invalido(client, db):
    token = _token_admin(client, db)
    r = client.get("/admin/logs/cron?fichero=otro", headers=_headers(token))
    assert r.status_code == 400


def test_logs_cron_lee_fichero(client, db, tmp_path, monkeypatch):
    token = _token_admin(client, db)
    (tmp_path / "bdns_check.log").write_text("linea1\nlinea2\n", encoding="utf-8")
    monkeypatch.setattr("backend.app.routers.admin.CRON_LOG_DIR", str(tmp_path))
    r = client.get("/admin/logs/cron?fichero=bdns&n=1", headers=_headers(token))
    assert r.status_code == 200
    assert r.json()["lineas"] == ["linea2"]


def test_logs_cron_fichero_no_disponible(client, db, tmp_path, monkeypatch):
    token = _token_admin(client, db)
    monkeypatch.setattr("backend.app.routers.admin.CRON_LOG_DIR", str(tmp_path))
    r = client.get("/admin/logs/cron?fichero=health", headers=_headers(token))
    assert r.status_code == 200
    assert r.json()["lineas"] == ["(archivo de log no disponible)"]


# ── Avisos ────────────────────────────────────────────────────────────────────

def test_listar_avisos_vacio(client, db):
    token = _token_admin(client, db)
    r = client.get("/admin/avisos", headers=_headers(token))
    assert r.status_code == 200
    assert r.json() == []


def test_listar_avisos_devuelve_sin_resolucion(client, db):
    token = _token_admin(client, db)
    _convocatoria(db, num_convoc="SIN-RESOL", fecha_resolucion=None)
    _convocatoria(db, num_convoc="CON-RESOL", fecha_resolucion=date(2025, 1, 1))
    r = client.get("/admin/avisos", headers=_headers(token))
    assert r.status_code == 200
    nums = [a["titulo_convoc"] for a in r.json()]
    assert any("prueba" in n.lower() for n in nums)
    # La convocatoria con resolución no debe aparecer
    assert len(r.json()) == 1


def test_desactivar_aviso(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db)
    r = client.patch(
        f"/admin/avisos/{convoc.id_convoc}/desactivar",
        headers=_headers(token),
    )
    assert r.status_code == 200
    # Ya no debe aparecer en la lista de avisos
    avisos = client.get("/admin/avisos", headers=_headers(token)).json()
    ids = [a["id_convoc"] for a in avisos]
    assert convoc.id_convoc not in ids


def test_fin_plazo_fija_fecha_y_calcula_estado(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db, anio_convocatoria=date.today().year)
    fin = (date.today() - timedelta(days=1)).isoformat()
    r = client.patch(
        f"/admin/avisos/{convoc.id_convoc}/fin-plazo",
        json={"fecha_fin_plazo": fin},
        headers=_headers(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fecha_fin_plazo"] == fin
    assert body["estado_plazo"] == "cerrado"


def test_fin_plazo_abierto(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db, anio_convocatoria=date.today().year)
    fin = (date.today() + timedelta(days=5)).isoformat()
    r = client.patch(
        f"/admin/avisos/{convoc.id_convoc}/fin-plazo",
        json={"fecha_fin_plazo": fin},
        headers=_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["estado_plazo"] == "abierto"


def test_fin_plazo_borrar_con_null(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db, anio_convocatoria=date.today().year,
                           fecha_fin_plazo=date.today())
    r = client.patch(
        f"/admin/avisos/{convoc.id_convoc}/fin-plazo",
        json={"fecha_fin_plazo": None},
        headers=_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["fecha_fin_plazo"] is None
    assert r.json()["estado_plazo"] == "sin_fecha"


def test_fin_plazo_convocatoria_inexistente_404(client, db):
    token = _token_admin(client, db)
    r = client.patch(
        "/admin/avisos/99999/fin-plazo",
        json={"fecha_fin_plazo": "2026-06-15"},
        headers=_headers(token),
    )
    assert r.status_code == 404


def test_fin_plazo_requiere_admin(client, db):
    token = _token_registrado(client, db)
    r = client.patch(
        "/admin/avisos/1/fin-plazo",
        json={"fecha_fin_plazo": "2026-06-15"},
        headers=_headers(token),
    )
    assert r.status_code == 403


def test_eliminar_aviso_sin_solicitudes(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db)
    r = client.delete(f"/admin/avisos/{convoc.id_convoc}", headers=_headers(token))
    assert r.status_code == 200


def test_eliminar_aviso_con_solicitudes_devuelve_409(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db)
    # Registrar un usuario y añadir una solicitud asociada a la convocatoria
    from backend.app.models import Beneficiario
    benef = Beneficiario(nombre="Entidad test", cif="G12345678", tipo_benef="asociacion")
    db.add(benef)
    db.commit()
    db.refresh(benef)
    solic = Solicitud(
        num_expediente="EXP-001",
        estado="concedida",
        id_convoc=convoc.id_convoc,
        id_benef=benef.id_benef,
    )
    db.add(solic)
    db.commit()

    r = client.delete(f"/admin/avisos/{convoc.id_convoc}", headers=_headers(token))
    assert r.status_code == 409


def test_reactivar_aviso(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db, fecha_resolucion=date(2025, 1, 1))

    r = client.patch(f"/admin/avisos/{convoc.id_convoc}/reactivar", headers=_headers(token))
    assert r.status_code == 200
    assert r.json()["fecha_resolucion"] is None

    avisos = client.get("/admin/avisos", headers=_headers(token)).json()
    assert any(a["id_convoc"] == convoc.id_convoc for a in avisos)


def test_reactivar_aviso_ya_activo_devuelve_400(client, db):
    token = _token_admin(client, db)
    convoc = _convocatoria(db, fecha_resolucion=None)
    r = client.patch(f"/admin/avisos/{convoc.id_convoc}/reactivar", headers=_headers(token))
    assert r.status_code == 400


def test_incluir_resueltas_devuelve_todas(client, db):
    token = _token_admin(client, db)
    _convocatoria(db, num_convoc="ACTIVA",   fecha_resolucion=None)
    _convocatoria(db, num_convoc="RESUELTA", fecha_resolucion=date(2025, 1, 1))

    sin_param = client.get("/admin/avisos", headers=_headers(token)).json()
    con_param = client.get("/admin/avisos?incluir_resueltas=true", headers=_headers(token)).json()

    assert len(con_param) > len(sin_param)


def test_aviso_inexistente_devuelve_404(client, db):
    token = _token_admin(client, db)
    r = client.patch("/admin/avisos/9999/desactivar", headers=_headers(token))
    assert r.status_code == 404


# ── Logs ──────────────────────────────────────────────────────────────────────

def test_logs_devuelve_lista(client, db):
    token = _token_admin(client, db)
    r = client.get("/admin/logs?n=10", headers=_headers(token))
    assert r.status_code == 200
    assert "lineas" in r.json()
    assert isinstance(r.json()["lineas"], list)


def test_logs_errores_devuelve_lista(client, db):
    token = _token_admin(client, db)
    r = client.get("/admin/logs/errores?n=10", headers=_headers(token))
    assert r.status_code == 200
    assert "lineas" in r.json()
    assert isinstance(r.json()["lineas"], list)


def test_logs_errores_requiere_admin(client, db):
    token = _token_registrado(client, db)
    r = client.get("/admin/logs/errores?n=10", headers=_headers(token))
    assert r.status_code == 403
