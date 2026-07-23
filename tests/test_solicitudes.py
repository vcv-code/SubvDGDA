import csv
import io
import pytest
from backend.app.models import Convocatoria, Beneficiario, Solicitud, Concesion


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


# --- Exportación CSV ---

def test_exportar_csv_content_type(client):
    response = client.get("/solicitudes/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


def test_exportar_csv_cabecera(client):
    response = client.get("/solicitudes/export")
    reader = csv.reader(io.StringIO(response.text))
    cabecera = next(reader)
    assert cabecera == ["anio", "tipo", "num_expediente", "entidad", "cif",
                        "estado", "importe", "linea", "tramo", "provincia", "ccaa",
                        "puntuacion", "es_agrupacion", "causa_exclusion"]


def test_exportar_csv_con_datos(db_con_datos, client):
    response = client.get("/solicitudes/export")
    reader = csv.reader(io.StringIO(response.text))
    filas = list(reader)
    # cabecera + 3 filas de datos
    assert len(filas) == 4


def test_exportar_csv_filtro_tipo(db_con_datos, client):
    response = client.get("/solicitudes/export?tipo=epa")
    reader = csv.reader(io.StringIO(response.text))
    filas = list(reader)[1:]  # sin cabecera
    assert len(filas) == 2
    assert all(f[1] == "epa" for f in filas)


def test_exportar_csv_disposition(client):
    response = client.get("/solicitudes/export")
    assert "attachment" in response.headers["content-disposition"]
    assert "solicitudes.csv" in response.headers["content-disposition"]


# --- Campo tramo ---

@pytest.fixture
def db_con_tramo(db):
    conv = Convocatoria(titulo_convoc="EELL 2025", tipo_convoc="eell", anio_convocatoria=2025, periodo_meses=12)
    db.add(conv)
    db.flush()
    benef = Beneficiario(cif="P99999001", nombre="Ayuntamiento de Prueba", tipo_benef="entidad_local")
    db.add(benef)
    db.flush()
    solic = Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXP-T2", estado="concedida")
    db.add(solic)
    db.flush()
    db.add(Concesion(id_solic=solic.id_solic, importe=30000, tramo=2))
    db.commit()
    return solic.id_solic


def test_tramo_aparece_en_respuesta(db_con_tramo, client):
    data = client.get("/solicitudes/?cif=P99999001").json()
    assert data["total"] == 1
    assert data["resultados"][0]["tramo"] == 2


def test_tramo_nulo_en_solicitud_sin_concesion(db_con_datos, client):
    data = client.get("/solicitudes/?estado=excluida").json()
    assert data["total"] >= 1
    assert all(r["tramo"] is None for r in data["resultados"])


# --- Causas de exclusión ---

@pytest.fixture
def db_con_causas(db):
    """Excluidas con códigos de causa + catálogo, para el buscador de exclusiones."""
    from backend.app.models import CausaExclusion

    conv = Convocatoria(titulo_convoc="EPA 2024", tipo_convoc="epa", anio_convocatoria=2024, periodo_meses=12)
    db.add(conv)
    db.flush()
    benef = Beneficiario(cif="G11111111", nombre="Asociación Test Causas", tipo_benef="asociacion")
    db.add(benef)
    db.flush()
    db.add_all([
        Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXC-6",   estado="excluida", causa_exclusion="6"),
        Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXC-16",  estado="excluida", causa_exclusion="16"),
        Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXC-6A",  estado="excluida", causa_exclusion="6.a"),
        Solicitud(id_convoc=conv.id_convoc, id_benef=benef.id_benef, num_expediente="EXC-269", estado="excluida", causa_exclusion="2;6;9"),
    ])
    db.add_all([
        CausaExclusion(tipo_convoc="epa", anio=2024, codigo="3.1", motivo="Solicitud fuera de plazo o no presentada por SIGES."),
        CausaExclusion(tipo_convoc="epa", anio=2024, codigo="7",   motivo="No acreditar inscripción de la entidad."),
        CausaExclusion(tipo_convoc="eell", anio=2023, codigo="5",  motivo="Solicitud presentada fuera de plazo.", articulo="5.1"),
    ])
    db.commit()


def test_causa_exclusion_en_respuesta(db_con_causas, client):
    data = client.get("/solicitudes/?estado=excluida").json()
    assert data["total"] == 4
    causas = {r["num_expediente"]: r["causa_exclusion"] for r in data["resultados"]}
    assert causas["EXC-269"] == "2;6;9"


def test_filtro_causa_token_exacto(db_con_causas, client):
    """El filtro causa=6 debe casar '6' y '2;6;9' pero NO '16' ni '6.a'."""
    data = client.get("/solicitudes/?causa=6").json()
    expedientes = {r["num_expediente"] for r in data["resultados"]}
    assert expedientes == {"EXC-6", "EXC-269"}


def test_filtro_causa_codigo_con_punto(db_con_causas, client):
    data = client.get("/solicitudes/?causa=6.a").json()
    expedientes = {r["num_expediente"] for r in data["resultados"]}
    assert expedientes == {"EXC-6A"}


def test_catalogo_causas_estructura(db_con_causas, client):
    response = client.get("/solicitudes/causas")
    assert response.status_code == 200
    data = response.json()
    assert data["epa"]["2024"]["7"]["motivo"] == "No acreditar inscripción de la entidad."
    assert data["epa"]["2024"]["7"]["articulo"] is None
    assert data["eell"]["2023"]["5"]["articulo"] == "5.1"


def test_catalogo_causas_cache(db_con_causas, client):
    response = client.get("/solicitudes/causas")
    assert "max-age=86400" in response.headers.get("cache-control", "")


def test_exportar_csv_incluye_causa(db_con_causas, client):
    response = client.get("/solicitudes/export?estado=excluida")
    filas = list(csv.reader(io.StringIO(response.text)))
    idx = filas[0].index("causa_exclusion")
    causas = {f[2]: f[idx] for f in filas[1:]}   # num_expediente -> causa
    assert causas["EXC-269"] == "2;6;9"
