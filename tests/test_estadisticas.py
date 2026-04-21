import pytest
from backend.app.models import Convocatoria, Beneficiario, Solicitud, Concesion


@pytest.fixture
def db_con_datos(db):
    conv = Convocatoria(titulo_convoc="EPA 2024", tipo_convoc="epa", anio_convocatoria=2024, periodo_meses=12)
    db.add(conv)
    db.flush()

    benef = Beneficiario(cif="G00000001", nombre="Asociación Test", tipo_benef="asociacion")
    db.add(benef)
    db.flush()

    solic_concedida = Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXP001", estado="concedida")
    solic_excluida  = Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXP002", estado="excluida")
    db.add_all([solic_concedida, solic_excluida])
    db.flush()

    db.add(Concesion(id_solic=solic_concedida.id_solic, importe=1000.00))
    db.commit()


def test_estadisticas_responde(client):
    response = client.get("/estadisticas/")
    assert response.status_code == 200


def test_estadisticas_estructura(client):
    # Verifica que el JSON tiene las claves esperadas aunque no haya datos
    data = client.get("/estadisticas/").json()
    assert "por_anio" in data
    assert "total_registros" in data
    assert "total_concedidas" in data
    assert "importe_global" in data


def test_estadisticas_totales(db_con_datos, client):
    data = client.get("/estadisticas/").json()
    assert data["total_registros"] == 2
    assert data["total_concedidas"] == 1
    assert data["importe_global"] == 1000.0


def test_estadisticas_por_anio(db_con_datos, client):
    data = client.get("/estadisticas/").json()
    assert len(data["por_anio"]) == 1
    fila = data["por_anio"][0]
    assert fila["anio"] == 2024
    assert fila["tipo"] == "epa"
    assert fila["concedidas"] == 1
    assert fila["excluidas"] == 1
