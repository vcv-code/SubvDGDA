import pytest
from backend.app.models import (
    Convocatoria, Beneficiario, Solicitud, Concesion, Agrupacion, AgrupacionMiembro
)


@pytest.fixture
def db_con_agrupacion(db):
    conv = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add(conv)
    db.flush()

    represent = Beneficiario(cif="P00000001", nombre="Ayuntamiento de Burgos", tipo_benef="entidad_local")
    miembro1  = Beneficiario(cif="P00000002", nombre="Ayuntamiento de Aranda", tipo_benef="entidad_local")
    db.add_all([represent, miembro1])
    db.flush()

    solic = Solicitud(id_convoc=conv.id_convoc, id_benef=represent.id_benef, num_expediente="EXP-AGRUP-01", estado="concedida")
    solic_sin_agrup = Solicitud(id_convoc=conv.id_convoc, id_benef=represent.id_benef, num_expediente="EXP-SIN-01", estado="concedida")
    db.add_all([solic, solic_sin_agrup])
    db.flush()

    conces = Concesion(id_solic=solic.id_solic, importe=50000)
    db.add(conces)
    db.flush()

    agrup = Agrupacion(id_conces=conces.id_conces, id_represent=represent.id_benef, num_municipios=2)
    db.add(agrup)
    db.flush()

    db.add(AgrupacionMiembro(id_agrup=agrup.id_agrup, id_benef=represent.id_benef, importe_asignado=30000))
    db.add(AgrupacionMiembro(id_agrup=agrup.id_agrup, id_benef=miembro1.id_benef,  importe_asignado=20000))
    db.commit()

    return {"id_con_agrup": solic.id_solic, "id_sin_agrup": solic_sin_agrup.id_solic}


def test_agrupacion_inexistente_devuelve_404(client):
    response = client.get("/agrupaciones/99999")
    assert response.status_code == 404


def test_agrupacion_solicitud_sin_concesion_devuelve_404(db_con_agrupacion, client):
    id_sin = db_con_agrupacion["id_sin_agrup"]
    response = client.get(f"/agrupaciones/{id_sin}")
    assert response.status_code == 404


def test_agrupacion_devuelve_estructura_correcta(db_con_agrupacion, client):
    id_con = db_con_agrupacion["id_con_agrup"]
    response = client.get(f"/agrupaciones/{id_con}")
    assert response.status_code == 200
    data = response.json()
    assert "id_agrup" in data
    assert "num_municipios" in data
    assert "representante" in data
    assert "miembros" in data


def test_agrupacion_num_municipios_correcto(db_con_agrupacion, client):
    id_con = db_con_agrupacion["id_con_agrup"]
    data = client.get(f"/agrupaciones/{id_con}").json()
    assert data["num_municipios"] == 2


def test_agrupacion_miembros_tienen_campos(db_con_agrupacion, client):
    id_con = db_con_agrupacion["id_con_agrup"]
    data = client.get(f"/agrupaciones/{id_con}").json()
    assert len(data["miembros"]) == 2
    for m in data["miembros"]:
        assert "nombre" in m
        assert "cif" in m
        assert "importe_asignado" in m
