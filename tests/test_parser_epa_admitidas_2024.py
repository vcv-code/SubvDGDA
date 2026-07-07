"""
Tests para el parser de admitidas EPA 2024 (parser_EPAs_admitidas_2024.py),
que extrae la línea de subvención (colonias felinas / animales abandonados).

Se prueban las funciones puras (normalizar_linea, detectar_seccion,
_parsear_buffer) y, como integración, el parseo del PDF real commiteado en
data/raw/epas/2024/ (se omite con skip si no está presente).
"""
import os

import pytest

from scripts.data_extractor.parser_EPAs_admitidas_2024 import (
    normalizar_linea,
    detectar_seccion,
    _parsear_buffer,
    parsear_admitidas_epa2024,
)

_PDF = "data/raw/epas/2024/relacion-def-admitidas-EPA2024.pdf"


# ─────────────────────────────────────────────
# normalizar_linea
# ─────────────────────────────────────────────

def test_normalizar_colonias():
    assert normalizar_linea("SÍ COLONIAS") == "colonias_felinas"
    assert normalizar_linea("COLONIAS") == "colonias_felinas"
    assert normalizar_linea("SI COLONIAS") == "colonias_felinas"

def test_normalizar_otros():
    assert normalizar_linea("SÍ OTROS") == "animales_abandonados"

def test_normalizar_no_aplica_y_vacio():
    assert normalizar_linea("No aplica") is None
    assert normalizar_linea("") is None
    assert normalizar_linea(None) is None


# ─────────────────────────────────────────────
# detectar_seccion
# ─────────────────────────────────────────────

def test_detectar_seccion_anexos():
    assert detectar_seccion("ANEXO I SOLICITUDES ADMITIDAS") == "admitidas"
    assert detectar_seccion("ANEXO II SOLICITUDES EXCLUIDAS") == "excluidas"
    assert detectar_seccion("ANEXO III – CAUSAS DE EXCLUSIÓN") == "causas"
    assert detectar_seccion("ANEXO IV SOLICITUDES DESISTIDAS") == "desistidas"

def test_detectar_seccion_fila_normal():
    assert detectar_seccion("2024B002 Asociacion El Gato Garduño G93705358 SÍ COLONIAS") is None


# ─────────────────────────────────────────────
# _parsear_buffer — la línea se lee DESPUÉS del CIF
# ─────────────────────────────────────────────

def test_buffer_basico():
    r = _parsear_buffer("2024B002", "Asociacion El Gato Garduño G93705358 SÍ COLONIAS")
    assert r["cif"] == "G93705358"
    assert r["linea"] == "colonias_felinas"

def test_buffer_nombre_con_colonias_pero_linea_otros():
    # El nombre contiene "COLONIAS" pero la línea real es OTROS: al anclar por CIF
    # no debe dejarse engañar por la palabra del nombre.
    r = _parsear_buffer("2024X001", "ASOC COLONIAS FELINAS DE EJEMPLO G12345678 SÍ OTROS")
    assert r["linea"] == "animales_abandonados"

def test_buffer_no_aplica():
    r = _parsear_buffer("2023B628", "ASOCIACION AMIBICHOS G45844933 No aplica")
    assert r["cif"] == "G45844933"
    assert r["linea"] is None

def test_buffer_nombre_multilinea():
    # El nombre parte en dos líneas de celda (se unen antes de parsear).
    r = _parsear_buffer("2024B116", "ASOC PARA LA DEFENSA Y PROTECCION DE LOS ANIMALES CANARIOS G38220455 SÍ OTROS")
    assert r["cif"] == "G38220455"
    assert r["linea"] == "animales_abandonados"


# ─────────────────────────────────────────────
# Integración: PDF real
# ─────────────────────────────────────────────

@pytest.mark.skipif(not os.path.exists(_PDF), reason="PDF de admitidas no disponible")
def test_integracion_pdf_real():
    regs = parsear_admitidas_epa2024(_PDF)
    mapa = {r["num_expediente"]: r["linea"] for r in regs}

    # Volumen razonable de admitidas
    assert len(regs) > 800

    # Valores concretos comprobables en el Anexo I
    assert mapa["2024B002"] == "colonias_felinas"       # El Gato Garduño
    assert mapa["2024B004"] == "animales_abandonados"   # COORDINADORA PROYECTO ESCAN
    assert mapa["2023B628"] is None                     # arrastre 2023: "No aplica"

    # Los 4 que extract_tables se saltaba deben resolverse por texto
    assert mapa["2024B003"] == "colonias_felinas"
    assert mapa["2024B007"] == "animales_abandonados"

    # No hay líneas espurias: solo los dos valores del enum o None
    valores = set(mapa.values())
    assert valores <= {"colonias_felinas", "animales_abandonados", None}
