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
                  "ccaa_top", "por_ccaa", "top_provincias", "concentracion",
                  "distribucion_importes", "recurrencia_por_anio",
                  "entidades_repiten", "total_entidades"):
        assert clave in data
    assert "top_10_pct" in data["concentracion"]
    assert "resto_pct" in data["concentracion"]


def test_eell_sin_datos_devuelve_ceros(client):
    data = client.get("/estadisticas/eell").json()
    assert data["pct_ayuntamientos_con_ayuda"] == 0.0
    assert data["importe_medio"] == 0.0
    assert data["por_ccaa"] == []
    assert data["top_provincias"] == []
    assert data["distribucion_importes"] == []
    assert data["recurrencia_por_anio"] == []
    assert data["entidades_repiten"] == 0
    assert data["total_entidades"] == 0


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


def test_eell_distribucion_importes(db_eell, client):
    # db_eell tiene dos concedidas de 10.000 y 20.000 € → ambas en el
    # tramo 10.000–25.000 €; el resto de tramos a 0.
    data = client.get("/estadisticas/eell").json()
    tramos = {t["rango"]: t["cantidad"] for t in data["distribucion_importes"]}
    assert tramos["10.000–25.000 €"] == 2
    assert tramos["< 10.000 €"] == 0
    assert tramos["≥ 75.000 €"] == 0
    # La suma de los tramos coincide con el nº de concesiones
    assert sum(tramos.values()) == 2


def test_eell_recurrencia_un_solo_anio(db_eell, client):
    # Un único año (2024): las 2 concedidas son nuevas, ninguna repite.
    data = client.get("/estadisticas/eell").json()
    assert data["entidades_repiten"] == 0
    assert data["total_entidades"] == 2
    rec = {r["anio"]: r for r in data["recurrencia_por_anio"]}
    assert rec[2024]["nuevas"] == 2
    assert rec[2024]["recurrentes"] == 0


@pytest.fixture
def db_eell_multianio(db):
    """Dos convocatorias EELL (2023 y 2024) con una entidad que repite."""
    c23 = Convocatoria(titulo_convoc="EELL 2023", tipo_convoc="eell", anio_convocatoria=2023, periodo_meses=12)
    c24 = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([c23, c24])
    db.flush()

    ba = Beneficiario(cif="P4100010A", nombre="Ayto. Repite",  tipo_benef="ayuntamiento")
    bb = Beneficiario(cif="P4100011B", nombre="Ayto. Nuevo24",  tipo_benef="ayuntamiento")
    db.add_all([ba, bb])
    db.flush()

    # ba concedida en 2023 y 2024 (repite); bb solo en 2024 (nueva ese año)
    sa23 = Solicitud(id_convoc=c23.id_convoc, id_benef=ba.id_benef, estado="concedida",
                     ccaa="Andalucía", provincia="Sevilla")
    sa24 = Solicitud(id_convoc=c24.id_convoc, id_benef=ba.id_benef, estado="concedida",
                     ccaa="Andalucía", provincia="Sevilla")
    sb24 = Solicitud(id_convoc=c24.id_convoc, id_benef=bb.id_benef, estado="concedida",
                     ccaa="Andalucía", provincia="Málaga")
    db.add_all([sa23, sa24, sb24])
    db.flush()

    db.add_all([
        Concesion(id_solic=sa23.id_solic, importe=50000.00),
        Concesion(id_solic=sa24.id_solic, importe=60000.00),
        Concesion(id_solic=sb24.id_solic, importe=30000.00),
    ])
    db.commit()


def test_eell_recurrencia_multianio(db_eell_multianio, client):
    data = client.get("/estadisticas/eell").json()
    # Una entidad (ba) recibe ayuda en 2 años → repite
    assert data["entidades_repiten"] == 1
    assert data["total_entidades"] == 2
    rec = {r["anio"]: r for r in data["recurrencia_por_anio"]}
    # 2023: solo ba, primera vez → 1 nueva, 0 recurrentes
    assert rec[2023]["nuevas"] == 1
    assert rec[2023]["recurrentes"] == 0
    # 2024: ba (recurrente) + bb (nueva) → 1 nueva, 1 recurrente
    assert rec[2024]["nuevas"] == 1
    assert rec[2024]["recurrentes"] == 1
    # El recurrente de 2024 es la entidad que ya estaba en 2023 (ba)
    assert rec[2024]["recurrentes_nombres"] == ["Ayto. Repite"]
    assert rec[2023]["recurrentes_nombres"] == []


# ─────────────────────────────────────────────────────────────
# TESTS — umbrales de puntuación (GET /estadisticas/)
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def db_umbrales(db):
    """EPA 2021 sin corte (todas concedidas) y EPA 2024 con corte y dos líneas."""
    c21 = Convocatoria(titulo_convoc="EPA 2021", tipo_convoc="epa", anio_convocatoria=2021, periodo_meses=12)
    c24 = Convocatoria(titulo_convoc="EPA 2024", tipo_convoc="epa", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([c21, c24])
    db.flush()

    bs = [Beneficiario(cif=f"G0000000{i}", nombre=f"Ent {i}", tipo_benef="asociacion") for i in range(1, 6)]
    db.add_all(bs)
    db.flush()

    # 2021: dos concedidas, ninguna no_beneficiaria → sin corte
    s1 = Solicitud(id_convoc=c21.id_convoc, id_benef=bs[0].id_benef, estado="concedida", puntuacion=50.0)
    s2 = Solicitud(id_convoc=c21.id_convoc, id_benef=bs[1].id_benef, estado="concedida", puntuacion=60.0)
    # 2024: dos concedidas (una por línea) + una no_beneficiaria → corte por línea
    s3 = Solicitud(id_convoc=c24.id_convoc, id_benef=bs[2].id_benef, estado="concedida", puntuacion=40.0)
    s4 = Solicitud(id_convoc=c24.id_convoc, id_benef=bs[3].id_benef, estado="concedida", puntuacion=45.0)
    s5 = Solicitud(id_convoc=c24.id_convoc, id_benef=bs[4].id_benef, estado="no_beneficiaria", puntuacion=35.0)
    db.add_all([s1, s2, s3, s4, s5])
    db.flush()

    db.add_all([
        Concesion(id_solic=s1.id_solic, importe=3000.0),
        Concesion(id_solic=s2.id_solic, importe=3000.0),
        Concesion(id_solic=s3.id_solic, importe=3000.0, linea="colonias_felinas"),
        Concesion(id_solic=s4.id_solic, importe=3000.0, linea="animales_abandonados"),
    ])
    db.commit()


def test_umbrales_en_estructura(client):
    assert "umbrales" in client.get("/estadisticas/").json()


def test_umbrales_sin_datos_lista_vacia(client):
    assert client.get("/estadisticas/").json()["umbrales"] == []


def test_umbrales_sin_corte(db_umbrales, client):
    # 2021 no tiene no_beneficiarias → todas las admitidas obtuvieron ayuda
    data = client.get("/estadisticas/").json()
    u = {(x["tipo"], x["anio"]): x for x in data["umbrales"]}
    assert u[("epa", 2021)]["hubo_corte"] is False
    assert u[("epa", 2021)]["umbral"] is None
    assert u[("epa", 2021)]["por_linea"] == []


def test_umbrales_con_corte_por_linea(db_umbrales, client):
    # 2024 tiene una no_beneficiaria → hubo corte; umbral = mín. concedida por línea
    data = client.get("/estadisticas/").json()
    u = {(x["tipo"], x["anio"]): x for x in data["umbrales"]}
    item = u[("epa", 2024)]
    assert item["hubo_corte"] is True
    por = {p["linea"]: p["umbral"] for p in item["por_linea"]}
    assert por["colonias_felinas"] == 40.0
    assert por["animales_abandonados"] == 45.0


# ─────────────────────────────────────────────────────────────
# TESTS — bloque de exclusiones (por año + causas frecuentes)
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def db_exclusiones(db):
    """Dos años EELL con excluidas y catálogo de causas; las causas frecuentes
    deben salir SOLO del último año (cada convocatoria numera distinto)."""
    from backend.app.models import CausaExclusion

    c23 = Convocatoria(titulo_convoc="EELL 2023", tipo_convoc="eell", anio_convocatoria=2023, periodo_meses=12)
    c24 = Convocatoria(titulo_convoc="EELL 2024", tipo_convoc="eell", anio_convocatoria=2024, periodo_meses=12)
    db.add_all([c23, c24])
    db.flush()

    b = Beneficiario(cif="P9900001X", nombre="Ayto. Prueba Exclusiones", tipo_benef="ayuntamiento")
    db.add(b)
    db.flush()

    db.add_all([
        # 2023: 1 excluida (no debe influir en causas_frecuentes)
        Solicitud(id_convoc=c23.id_convoc, id_benef=b.id_benef, num_expediente="E23-1",
                  estado="excluida", causa_exclusion="5"),
        # 2024: 3 excluidas → B aparece 3 veces, F 1 vez
        Solicitud(id_convoc=c24.id_convoc, id_benef=b.id_benef, num_expediente="E24-1",
                  estado="excluida", causa_exclusion="B"),
        Solicitud(id_convoc=c24.id_convoc, id_benef=b.id_benef, num_expediente="E24-2",
                  estado="excluida", causa_exclusion="B;F"),
        Solicitud(id_convoc=c24.id_convoc, id_benef=b.id_benef, num_expediente="E24-3",
                  estado="excluida", causa_exclusion="B"),
        # una concedida para que el resto del endpoint tenga datos
        Solicitud(id_convoc=c24.id_convoc, id_benef=b.id_benef, num_expediente="E24-OK",
                  estado="concedida", ccaa="Andalucía", provincia="Sevilla"),
    ])
    db.add_all([
        CausaExclusion(tipo_convoc="eell", anio=2024, codigo="B", motivo="Sin Programa de Gestión Ética aprobado."),
        CausaExclusion(tipo_convoc="eell", anio=2024, codigo="F", motivo="Cronograma no conforme al Anexo II."),
    ])
    db.commit()


def test_exclusiones_por_anio(db_exclusiones, client):
    data = client.get("/estadisticas/eell").json()
    por_anio = {x["anio"]: x["total"] for x in data["exclusiones"]["por_anio"]}
    assert por_anio == {2023: 1, 2024: 3}


def test_exclusiones_causas_solo_ultimo_anio(db_exclusiones, client):
    """Las causas frecuentes son del último año; el "5" de 2023 no aparece."""
    data = client.get("/estadisticas/eell").json()
    exc = data["exclusiones"]
    assert exc["causas_anio"] == 2024
    causas = {c["codigo"]: c for c in exc["causas_frecuentes"]}
    assert set(causas) == {"B", "F"}
    assert causas["B"]["total"] == 3          # multivalor "B;F" suma en ambas
    assert causas["F"]["total"] == 1
    assert causas["B"]["motivo"] == "Sin Programa de Gestión Ética aprobado."


def test_exclusiones_vacio_sin_datos(client):
    """Sin excluidas, el bloque llega vacío y el endpoint no falla."""
    data = client.get("/estadisticas/eell").json()
    assert data["exclusiones"] == {"por_anio": [], "causas_anio": None, "causas_frecuentes": []}
