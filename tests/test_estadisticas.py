import pytest
from backend.app.models import Convocatoria, Beneficiario, Solicitud, Concesion


# ─────────────────────────────────────────────────────────────
# FIXTURES COMPARTIDAS
# ─────────────────────────────────────────────────────────────

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


@pytest.fixture
def db_epas(db):
    """Dos años EPA con tres beneficiarios para verificar nuevos/recurrentes."""
    conv23 = Convocatoria(titulo_convoc="EPA 2023", tipo_convoc="epa", anio_convocatoria=2023, periodo_meses=12)
    conv24 = Convocatoria(titulo_convoc="EPA 2024", tipo_convoc="epa", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([conv23, conv24])
    db.flush()

    b1 = Beneficiario(cif="G11111111", nombre="Protectora A", tipo_benef="asociacion")
    b2 = Beneficiario(cif="G22222222", nombre="Protectora B", tipo_benef="asociacion")
    b3 = Beneficiario(cif="G33333333", nombre="Protectora C", tipo_benef="asociacion")
    db.add_all([b1, b2, b3])
    db.flush()

    # 2023: b1 y b2 concedidas
    s1 = Solicitud(id_convoc=conv23.id_convoc, id_benef=b1.id_benef, estado="concedida")
    s2 = Solicitud(id_convoc=conv23.id_convoc, id_benef=b2.id_benef, estado="concedida")
    # 2024: b1 y b2 recurrentes, b3 nueva
    s3 = Solicitud(id_convoc=conv24.id_convoc, id_benef=b1.id_benef, estado="concedida")
    s4 = Solicitud(id_convoc=conv24.id_convoc, id_benef=b2.id_benef, estado="concedida")
    s5 = Solicitud(id_convoc=conv24.id_convoc, id_benef=b3.id_benef, estado="concedida")
    db.add_all([s1, s2, s3, s4, s5])
    db.flush()

    db.add_all([
        Concesion(id_solic=s1.id_solic, importe=2000.00),
        Concesion(id_solic=s2.id_solic, importe=4000.00),
        Concesion(id_solic=s3.id_solic, importe=3000.00),
        Concesion(id_solic=s4.id_solic, importe=5000.00),
        Concesion(id_solic=s5.id_solic, importe=1000.00),
    ])
    db.commit()


@pytest.fixture
def db_eell(db):
    """Una convocatoria EELL con solicitudes de distintas CCAA y estados."""
    conv = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add(conv)
    db.flush()

    ba = Beneficiario(cif="P4100001A", nombre="Ayto. Sevilla",  tipo_benef="ayuntamiento")
    bb = Beneficiario(cif="P4100002B", nombre="Ayto. Málaga",   tipo_benef="ayuntamiento")
    bc = Beneficiario(cif="P0800001C", nombre="Ayto. Toledo",   tipo_benef="ayuntamiento")
    bd = Beneficiario(cif="P0800002D", nombre="Ayto. Albacete", tipo_benef="ayuntamiento")
    db.add_all([ba, bb, bc, bd])
    db.flush()

    # ba y bb concedidas (Andalucía); bc excluida; bd desistida
    sa = Solicitud(id_convoc=conv.id_convoc, id_benef=ba.id_benef, estado="concedida",
                   ccaa="Andalucía", provincia="Sevilla")
    sb = Solicitud(id_convoc=conv.id_convoc, id_benef=bb.id_benef, estado="concedida",
                   ccaa="Andalucía", provincia="Málaga")
    sc = Solicitud(id_convoc=conv.id_convoc, id_benef=bc.id_benef, estado="excluida",
                   ccaa="Castilla-La Mancha", provincia="Toledo")
    sd = Solicitud(id_convoc=conv.id_convoc, id_benef=bd.id_benef, estado="desistida",
                   ccaa="Castilla-La Mancha", provincia="Albacete")
    db.add_all([sa, sb, sc, sd])
    db.flush()

    db.add_all([
        Concesion(id_solic=sa.id_solic, importe=10000.00),
        Concesion(id_solic=sb.id_solic, importe=20000.00),
    ])
    db.commit()


# ─────────────────────────────────────────────────────────────
# TESTS — GET /estadisticas/
# ─────────────────────────────────────────────────────────────

def test_estadisticas_responde(client):
    response = client.get("/estadisticas/")
    assert response.status_code == 200


def test_estadisticas_estructura(client):
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


# ─────────────────────────────────────────────────────────────
# TESTS — GET /estadisticas/epas
# ─────────────────────────────────────────────────────────────

def test_epas_responde(client):
    assert client.get("/estadisticas/epas").status_code == 200


def test_epas_estructura(client):
    data = client.get("/estadisticas/epas").json()
    for clave in ("importe_medio", "mediana", "beneficiarios_unicos",
                  "nuevas_entidades", "distribucion_importes", "por_anio"):
        assert clave in data


def test_epas_sin_datos_devuelve_ceros(client):
    data = client.get("/estadisticas/epas").json()
    assert data["importe_medio"] == 0.0
    assert data["mediana"] == 0.0
    assert data["nuevas_entidades"] == 0
    assert data["distribucion_importes"] == []
    assert data["por_anio"] == []


def test_epas_calculos_globales(db_epas, client):
    # importes: 2000, 4000, 3000, 5000, 1000 → media=3000, mediana=3000
    data = client.get("/estadisticas/epas").json()
    assert data["importe_medio"] == 3000.0
    assert data["mediana"] == 3000.0
    assert data["beneficiarios_unicos"] == 3


def test_epas_nuevas_entidades(db_epas, client):
    # b3 aparece por primera vez en 2024 (año más reciente)
    data = client.get("/estadisticas/epas").json()
    assert data["nuevas_entidades"] == 1


def test_epas_nuevos_vs_recurrentes_por_anio(db_epas, client):
    data = client.get("/estadisticas/epas").json()
    anios = {a["anio"]: a for a in data["por_anio"]}

    # 2023: los tres beneficiarios son nuevos (es su primer año)
    assert anios[2023]["nuevos"] == 2
    assert anios[2023]["recurrentes"] == 0

    # 2024: b1 y b2 son recurrentes; b3 es nueva
    assert anios[2024]["nuevos"] == 1
    assert anios[2024]["recurrentes"] == 2


def test_epas_top_beneficiarios(db_epas, client):
    data = client.get("/estadisticas/epas").json()
    anio_2024 = next(a for a in data["por_anio"] if a["anio"] == 2024)
    top = anio_2024["top_beneficiarios"]
    assert len(top) > 0
    # El primero debe ser el de mayor importe (b2: 5000€)
    assert top[0]["importe"] == 5000.0
    assert top[0]["nombre"] == "Protectora B"


def test_epas_distribucion_tiene_todos_los_rangos(db_epas, client):
    data = client.get("/estadisticas/epas").json()
    rangos = [d["rango"] for d in data["distribucion_importes"]]
    # 5 rangos desde la corrección que eliminó "> 10.000 €" (importe máximo real = 10.000 €)
    assert len(rangos) == 5
    # Test data: 1000, 2000, 3000, 4000, 5000 €
    # < 2.000: 1000 → 1; 2.000–4.000: 2000,3000 → 2; 4.000–6.000: 4000,5000 → 2
    rango_menor = next(d for d in data["distribucion_importes"] if d["rango"].startswith("<"))
    assert rango_menor["cantidad"] == 1
    rango_2_4 = next(d for d in data["distribucion_importes"] if d["rango"].startswith("2.000"))
    assert rango_2_4["cantidad"] == 2


def test_epas_cache_header(client):
    r = client.get("/estadisticas/epas")
    assert "max-age" in r.headers.get("cache-control", "")


# ─────────────────────────────────────────────────────────────
# TESTS — GET /estadisticas/eell
# ─────────────────────────────────────────────────────────────

def test_eell_responde(client):
    assert client.get("/estadisticas/eell").status_code == 200


def test_eell_estructura(client):
    data = client.get("/estadisticas/eell").json()
    for clave in ("pct_ayuntamientos_con_ayuda", "importe_medio", "ratio_exclusion",
                  "ccaa_top", "por_ccaa", "top_provincias", "concentracion"):
        assert clave in data
    assert "top_10_pct" in data["concentracion"]
    assert "resto_pct" in data["concentracion"]


def test_eell_sin_datos_devuelve_ceros(client):
    data = client.get("/estadisticas/eell").json()
    assert data["pct_ayuntamientos_con_ayuda"] == 0.0
    assert data["importe_medio"] == 0.0
    assert data["por_ccaa"] == []
    assert data["top_provincias"] == []


def test_eell_pct_ayuntamientos(db_eell, client):
    # 2 de 4 solicitantes obtuvieron ayuda → 50 %
    data = client.get("/estadisticas/eell").json()
    assert data["pct_ayuntamientos_con_ayuda"] == 50.0


def test_eell_importe_medio(db_eell, client):
    # (10000 + 20000) / 2 = 15000
    data = client.get("/estadisticas/eell").json()
    assert data["importe_medio"] == 15000.0


def test_eell_ratio_exclusion(db_eell, client):
    # 2 excluidas+desistidas de 4 totales → 0.5
    data = client.get("/estadisticas/eell").json()
    assert data["ratio_exclusion"] == 0.5


def test_eell_ccaa_top(db_eell, client):
    # Andalucía acumula 30000€, es la CCAA con más importe
    data = client.get("/estadisticas/eell").json()
    assert data["ccaa_top"] == "Andalucía"


def test_eell_por_ccaa(db_eell, client):
    data = client.get("/estadisticas/eell").json()
    ccaa_map = {c["ccaa"]: c for c in data["por_ccaa"]}
    assert "Andalucía" in ccaa_map
    assert ccaa_map["Andalucía"]["importe_total"] == 30000.0
    assert ccaa_map["Andalucía"]["num_concesiones"] == 2


def test_eell_top_provincias(db_eell, client):
    data = client.get("/estadisticas/eell").json()
    provincias = {p["provincia"]: p["importe_total"] for p in data["top_provincias"]}
    assert provincias["Sevilla"] == 10000.0
    assert provincias["Málaga"] == 20000.0


def test_eell_concentracion_suma_100(db_eell, client):
    data = client.get("/estadisticas/eell").json()
    c = data["concentracion"]
    assert abs(c["top_10_pct"] + c["resto_pct"] - 100.0) < 0.1


def test_eell_cache_header(client):
    r = client.get("/estadisticas/eell")
    assert "max-age" in r.headers.get("cache-control", "")
