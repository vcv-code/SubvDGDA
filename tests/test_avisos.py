from datetime import date, timedelta

import pytest
from backend.app.models import Convocatoria


@pytest.fixture
def db_con_avisos(db):
    anio = date.today().year
    anio_pasado = anio - 1

    # Convocatoria de este año sin resolución → debe aparecer como aviso
    eell_pendiente = Convocatoria(
        num_convoc="BDNS-TEST-EELL",
        titulo_convoc="Subvenciones a entidades locales de protección animal",
        tipo_convoc="eell",
        anio_convocatoria=anio,
        fecha_convocatoria=date(anio, 4, 7),
        fecha_resolucion=None,
        periodo_meses=12,
    )
    # Convocatoria de este año ya resuelta → NO debe aparecer
    epa_resuelta = Convocatoria(
        num_convoc="BDNS-TEST-EPA-OLD",
        titulo_convoc="Subvenciones a entidades privadas de protección animal",
        tipo_convoc="epa",
        anio_convocatoria=anio,
        fecha_convocatoria=date(anio, 5, 5),
        fecha_resolucion=date(anio, 11, 30),
        periodo_meses=12,
    )
    # Convocatoria del año pasado sin resolución → NO debe aparecer (año distinto)
    vieja_pendiente = Convocatoria(
        num_convoc="BDNS-TEST-VIEJA",
        titulo_convoc="Subvenciones EELL año anterior",
        tipo_convoc="eell",
        anio_convocatoria=anio_pasado,
        fecha_convocatoria=date(anio_pasado, 3, 29),
        fecha_resolucion=None,
        periodo_meses=12,
    )
    db.add_all([eell_pendiente, epa_resuelta, vieja_pendiente])
    db.commit()
    return {"id_pendiente": eell_pendiente.id_convoc}


def test_avisos_devuelve_lista(client):
    response = client.get("/avisos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_avisos_sin_datos_devuelve_lista_vacia(client):
    response = client.get("/avisos/")
    assert response.json() == []


def test_avisos_solo_devuelve_pendientes_anio_actual(db_con_avisos, client):
    response = client.get("/avisos/")
    assert response.status_code == 200
    data = response.json()
    # Solo debe aparecer la EELL pendiente, no la resuelta ni la del año pasado
    assert len(data) == 1
    assert data[0]["tipo_convoc"] == "eell"


def test_avisos_estructura_correcta(db_con_avisos, client):
    data = client.get("/avisos/").json()
    aviso = data[0]
    assert "id_convoc" in aviso
    assert "titulo_convoc" in aviso
    assert "tipo_convoc" in aviso
    assert "anio_convocatoria" in aviso
    assert "fecha_convocatoria" in aviso


def test_avisos_anio_coincide_con_actual(db_con_avisos, client):
    data = client.get("/avisos/").json()
    anio_actual = date.today().year
    for aviso in data:
        assert aviso["anio_convocatoria"] == anio_actual


def test_avisos_no_incluye_convocatorias_resueltas(db_con_avisos, client):
    data = client.get("/avisos/").json()
    tipos = [a["tipo_convoc"] for a in data]
    # La EPA ya tiene fecha_resolucion → no debe aparecer
    assert "epa" not in tipos


# ── Estado del plazo de solicitud (fecha_fin_plazo → estado_plazo) ──────────

def _crear_pendiente(db, fin_plazo):
    """Inserta una convocatoria EELL del año actual, sin resolución, con la
    fecha de fin de plazo indicada. Devuelve nada; el aviso se consulta vía API."""
    anio = date.today().year
    db.add(Convocatoria(
        num_convoc="BDNS-TEST-PLAZO",
        titulo_convoc="Convocatoria de prueba de plazo",
        tipo_convoc="eell",
        anio_convocatoria=anio,
        fecha_convocatoria=date(anio, 4, 1),
        fecha_fin_plazo=fin_plazo,
        fecha_resolucion=None,
        periodo_meses=12,
    ))
    db.commit()


def test_avisos_estado_plazo_sin_fecha(db_con_avisos, client):
    """La convocatoria del fixture no tiene fecha_fin_plazo → 'sin_fecha'."""
    aviso = client.get("/avisos/").json()[0]
    assert "fecha_fin_plazo" in aviso
    assert aviso["estado_plazo"] == "sin_fecha"


def test_avisos_estado_plazo_abierto(db, client):
    _crear_pendiente(db, date.today() + timedelta(days=10))
    aviso = client.get("/avisos/").json()[0]
    assert aviso["estado_plazo"] == "abierto"


def test_avisos_estado_plazo_cerrado(db, client):
    _crear_pendiente(db, date.today() - timedelta(days=1))
    aviso = client.get("/avisos/").json()[0]
    assert aviso["estado_plazo"] == "cerrado"


def test_avisos_estado_plazo_hoy_es_abierto(db, client):
    """El último día del plazo (hoy == fin) aún cuenta como abierto."""
    _crear_pendiente(db, date.today())
    aviso = client.get("/avisos/").json()[0]
    assert aviso["estado_plazo"] == "abierto"
