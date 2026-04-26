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
