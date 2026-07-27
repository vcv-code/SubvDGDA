"""
Tests unitarios para las funciones de normalización de unificar_datasets.py.

Se prueban las transformaciones puras (sin I/O ni BD): normalización de
estados EPA y EELL, limpieza de importes, entidades y puntuaciones.
"""
import pytest
from scripts.data_processing.unificar_datasets import (
    normalizar_estado_epa,
    normalizar_estado_eell,
    limpiar_importe,
    limpiar_entidad,
    limpiar_puntuacion,
    limpiar_estado,
    indexar_solicitudes_epa,
    resolver_anio_epa,
)


# ─────────────────────────────────────────────
# normalizar_estado_epa
# El BOE llama "denegada" a dos realidades distintas según el año.
# ─────────────────────────────────────────────

def test_denegada_hasta_2023_es_excluida():
    assert normalizar_estado_epa("denegada", 2021) == "excluida"
    assert normalizar_estado_epa("denegada", 2022) == "excluida"
    assert normalizar_estado_epa("denegada", 2023) == "excluida"

def test_denegada_desde_2024_es_no_beneficiaria():
    assert normalizar_estado_epa("denegada", 2024) == "no_beneficiaria"
    assert normalizar_estado_epa("denegada", 2025) == "no_beneficiaria"

def test_otros_estados_epa_no_cambian():
    for estado in ("concedida", "excluida", "desistida", "no_beneficiaria"):
        assert normalizar_estado_epa(estado, 2024) == estado
        assert normalizar_estado_epa(estado, 2021) == estado


# ─────────────────────────────────────────────
# normalizar_estado_eell
# Concedida con importe 0 → no_beneficiaria (datos PDF sin importe real).
# ─────────────────────────────────────────────

def test_concedida_sin_importe_es_no_beneficiaria():
    assert normalizar_estado_eell("concedida", 0.0) == "no_beneficiaria"
    assert normalizar_estado_eell("concedida", None) == "no_beneficiaria"

def test_concedida_con_importe_permanece():
    assert normalizar_estado_eell("concedida", 5000.0) == "concedida"

def test_otros_estados_eell_no_cambian():
    for estado in ("excluida", "desistida", "no_beneficiaria"):
        assert normalizar_estado_eell(estado, 0.0) == estado


# ─────────────────────────────────────────────
# limpiar_importe
# ─────────────────────────────────────────────

def test_importe_none_da_cero():
    assert limpiar_importe(None) == 0.0

def test_importe_string_vacio_da_cero():
    assert limpiar_importe("") == 0.0

def test_importe_float_valido():
    assert limpiar_importe(3445.36) == 3445.36

def test_importe_entero():
    assert limpiar_importe(1000) == 1000.0

def test_importe_no_parseable_da_cero():
    assert limpiar_importe("no es un número") == 0.0


# ─────────────────────────────────────────────
# limpiar_entidad
# ─────────────────────────────────────────────

def test_entidad_none_da_none():
    assert limpiar_entidad(None) is None

def test_entidad_vacia_da_none():
    assert limpiar_entidad("") is None
    assert limpiar_entidad("   ") is None

def test_entidad_none_string_da_none():
    assert limpiar_entidad("None") is None

def test_entidad_normal_queda_igual():
    assert limpiar_entidad("  Asociación Gatos Madrid  ") == "Asociación Gatos Madrid"


# ─────────────────────────────────────────────
# limpiar_puntuacion
# ─────────────────────────────────────────────

def test_puntuacion_none_da_none():
    assert limpiar_puntuacion(None) is None

def test_puntuacion_float():
    assert limpiar_puntuacion(76.5) == 76.5

def test_puntuacion_no_numerica_da_none():
    assert limpiar_puntuacion("no válido") is None


# ─────────────────────────────────────────────
# limpiar_estado
# ─────────────────────────────────────────────

def test_estado_none_da_none():
    assert limpiar_estado(None) is None

def test_estado_vacio_da_none():
    assert limpiar_estado("") is None

def test_estado_normaliza_a_minusculas():
    assert limpiar_estado("Concedida") == "concedida"
    assert limpiar_estado("EXCLUIDA") == "excluida"


# ─────────────────────────────────────────────
# resolver_anio_epa
# Resoluciones tardías: una solicitud del año N cuya resolución no se publica
# hasta el BOE de N+1 debe atribuirse a la convocatoria N, no al fichero N+1.
# Solo se reatribuye si el mismo expediente Y el mismo CIF están en el año N.
# ─────────────────────────────────────────────

@pytest.fixture
def indice_epa():
    """Réplica reducida del dataset real con los cuatro casos cross-year."""
    return indexar_solicitudes_epa({
        2021: [
            # El BOE de 2021 publica un expediente numerado como 2022...
            {"num_expediente": "SUBV2022021", "cif": "G01779131"},
            # ...y otro con errata de año en el número (2032).
            {"num_expediente": "SUBV2032021", "cif": "G98657232"},
        ],
        2022: [
            # Mismo número que en 2021 pero OTRA entidad: el BOE lo reutilizó.
            {"num_expediente": "SUBV2022021", "cif": "G66561812"},
            {"num_expediente": "SUBV2022659", "cif": "G90180365"},
        ],
        2023: [
            {"num_expediente": "2023B628", "cif": "G45844933"},
            # Resolución tardía del expediente de 2022, misma entidad.
            {"num_expediente": "SUBV2022659", "cif": "G90180365"},
        ],
        2024: [
            # Resolución tardía del expediente de 2023, misma entidad.
            {"num_expediente": "2023B628", "cif": "G45844933"},
        ],
    })


def test_anio_declarado_igual_al_fichero_no_cambia(indice_epa):
    item = {"anio": 2023, "num_expediente": "2023B628", "cif": "G45844933"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2023

def test_sin_anio_declarado_usa_el_del_fichero(indice_epa):
    item = {"anio": None, "num_expediente": "LO_QUE_SEA", "cif": "G00000000"}
    assert resolver_anio_epa(item, 2025, indice_epa) == 2025

def test_resolucion_tardia_se_reatribuye_a_su_convocatoria(indice_epa):
    """La Sexta Huella: expediente de 2022 resuelto en el BOE de 2023."""
    item = {"anio": 2022, "num_expediente": "SUBV2022659", "cif": "G90180365"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2022

def test_resolucion_tardia_de_2023_resuelta_en_2024(indice_epa):
    """Amibichos: expediente de 2023 resuelto en el BOE de 2024."""
    item = {"anio": 2023, "num_expediente": "2023B628", "cif": "G45844933"}
    assert resolver_anio_epa(item, 2024, indice_epa) == 2023

def test_numero_reutilizado_por_otra_entidad_no_se_reatribuye(indice_epa):
    """SUBV2022021: mismo número en 2021 y 2022 pero CIF distinto.

    Es el falso positivo que justifica comprobar el CIF: sin esa comprobación
    ambas entidades colapsarían bajo la misma clave de deduplicación.
    """
    item = {"anio": 2022, "num_expediente": "SUBV2022021", "cif": "G01779131"}
    assert resolver_anio_epa(item, 2021, indice_epa) == 2021

def test_anio_con_errata_no_se_reatribuye(indice_epa):
    """SUBV2032021: declara 2032, año para el que no hay fichero."""
    item = {"anio": 2032, "num_expediente": "SUBV2032021", "cif": "G98657232"}
    assert resolver_anio_epa(item, 2021, indice_epa) == 2021

def test_mismo_expediente_distinto_cif_no_se_reatribuye(indice_epa):
    """Aunque el año declarado exista, si el CIF no casa se queda en su fichero."""
    item = {"anio": 2022, "num_expediente": "SUBV2022659", "cif": "G99999999"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2023

def test_indice_agrupa_por_anio_de_fichero(indice_epa):
    assert ("SUBV2022659", "G90180365") in indice_epa[2022]
    assert ("SUBV2022659", "G90180365") not in indice_epa[2021]
