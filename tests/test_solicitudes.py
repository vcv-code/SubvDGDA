import pytest
from backend.app.models import Convocatoria, Beneficiario, Solicitud


@pytest.fixture
def db_con_datos(db):
    """Inserta datos mínimos para testear filtros y paginación."""
    conv_epa  = Convocatoria(titulo_convoc="EPA 2024",  tipo_convoc="epa",  anio_convocatoria=2024, periodo_meses=12)
    conv_eell = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([conv_epa, conv_eell])
    db.flush()

    benef_a = Beneficiario(cif="G00000001", nombre="Asociación Protectora Gatos Madrid", tipo_benef="asociacion")
    benef_b = Beneficiario(cif="P00000001", nombre="Ayuntamiento de Burgos",              tipo_benef="entidad_local")
    db.add_all([benef_a, benef_b])
    db.flush()

    db.add_all([
        Solicitud(id_convoc=conv_epa.id_convoc,  id_benef=benef_a.id_benef, num_expediente="EXP001", estado="concedida"),
        Solicitud(id_convoc=conv_epa.id_convoc,  id_benef=benef_a.id_benef, num_expediente="EXP002", estado="excluida"),
        Solicitud(id_convoc=conv_eell.id_convoc, id_benef=benef_b.id_benef, num_expediente="EXP003", estado="concedida"),
    ])
    db.commit()


def test_solicitudes_responde(client):
    response = client.get("/solicitudes/")
    assert response.status_code == 200


def test_solicitudes_estructura_paginada(client):
    data = client.get("/solicitudes/").json()
    assert "total" in data
    assert "resultados" in data
    assert isinstance(data["resultados"], list)


def test_solicitudes_filtro_tipo(db_con_datos, client):
    response = client.get("/solicitudes/?tipo=epa")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(r["convocatoria"]["tipo_convoc"] == "epa" for r in data["resultados"])


def test_solicitudes_filtro_estado(db_con_datos, client):
    response = client.get("/solicitudes/?estado=concedida")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(r["estado"] == "concedida" for r in data["resultados"])


def test_solicitudes_paginacion(db_con_datos, client):
    response = client.get("/solicitudes/?limite=2&pagina=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["resultados"]) == 2

    response2 = client.get("/solicitudes/?limite=2&pagina=2")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total"] == 3
    assert len(data2["resultados"]) == 1


def test_solicitudes_filtro_cif(db_con_datos, client):
    response = client.get("/solicitudes/?cif=G00000001")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(r["beneficiario"]["cif"] == "G00000001" for r in data["resultados"])


def test_solicitudes_buscar_parcial(db_con_datos, client):
    response = client.get("/solicitudes/?buscar=Protectora")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Protectora" in r["beneficiario"]["nombre"] for r in data["resultados"])


def test_solicitudes_buscar_stopword_ignorada(db_con_datos, client):
    # "de" es stopword, busca igual que buscar=Burgos
    response_con = client.get("/solicitudes/?buscar=Ayuntamiento de Burgos")
    response_sin = client.get("/solicitudes/?buscar=Burgos")
    assert response_con.json() == response_sin.json()


def test_solicitudes_buscar_sin_resultados(db_con_datos, client):
    response = client.get("/solicitudes/?buscar=Inexistente")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["resultados"] == []
