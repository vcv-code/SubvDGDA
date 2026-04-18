import pytest
from backend.app.models import Convocatoria, Beneficiario, Solicitud


@pytest.fixture
def db_con_datos(db):
    """Inserta datos mínimos para testear filtros y paginación."""
    conv_epa  = Convocatoria(titulo_convoc="EPA 2024",  tipo_convoc="epa",  anio_convocatoria=2024, periodo_meses=12)
    conv_eell = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([conv_epa, conv_eell])
    db.flush()

    benef = Beneficiario(cif="G00000001", nombre="Asociación Test", tipo_benef="asociacion")
    db.add(benef)
    db.flush()

    db.add_all([
        Solicitud(id_convoc=conv_epa.id_convoc,  id_benef=benef.id_benef, num_expediente="EXP001", estado="concedida"),
        Solicitud(id_convoc=conv_epa.id_convoc,  id_benef=benef.id_benef, num_expediente="EXP002", estado="excluida"),
        Solicitud(id_convoc=conv_eell.id_convoc, id_benef=benef.id_benef, num_expediente="EXP003", estado="concedida"),
    ])
    db.commit()


def test_solicitudes_responde(client):
    response = client.get("/solicitudes/")
    assert response.status_code == 200


def test_solicitudes_devuelve_lista(client):
    response = client.get("/solicitudes/")
    assert isinstance(response.json(), list)


def test_solicitudes_filtro_tipo(db_con_datos, client):
    response = client.get("/solicitudes/?tipo=epa")
    assert response.status_code == 200
    resultados = response.json()
    assert len(resultados) == 2
    assert all(r["convocatoria"]["tipo_convoc"] == "epa" for r in resultados)


def test_solicitudes_filtro_estado(db_con_datos, client):
    response = client.get("/solicitudes/?estado=concedida")
    assert response.status_code == 200
    resultados = response.json()
    assert len(resultados) == 2
    assert all(r["estado"] == "concedida" for r in resultados)


def test_solicitudes_paginacion(db_con_datos, client):
    # Con limite=2 solo deben volver 2 resultados aunque haya 3
    response = client.get("/solicitudes/?limite=2&pagina=1")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # La segunda página tiene 1 resultado
    response2 = client.get("/solicitudes/?limite=2&pagina=2")
    assert response2.status_code == 200
    assert len(response2.json()) == 1
