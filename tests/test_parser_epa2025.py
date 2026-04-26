"""
Tests unitarios para el parser EPA 2025 (parser_EPAs_BOE_2025.py).

Se prueban las funciones puras de detección y extracción sin llamadas
a internet: mapear_indices, normalizar_linea, extraer_entidad_2025 y
los helpers de clasificación (_parece_numero_europeo, _es_cif,
_es_expediente). También se verifica, con un XML mínimo local, que la
corrección de estado (ANEXO IV leído como concedida en lugar de
denegada) está bien resuelta.
"""
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from scripts.data_extractor.parser_EPAs_BOE_2025 import (
    mapear_indices,
    normalizar_linea,
    extraer_entidad_2025,
    _parece_numero_europeo,
    _es_cif,
    _es_expediente,
    parsear_boe_epa_2025,
)


# ─────────────────────────────────────────────
# _parece_numero_europeo
# ─────────────────────────────────────────────

def test_numero_europeo_con_coma_y_puntos():
    assert _parece_numero_europeo("3.404,35") is True

def test_numero_europeo_sin_coma():
    assert _parece_numero_europeo("3404") is False

def test_numero_europeo_texto_normal():
    assert _parece_numero_europeo("Asociación Gatos Madrid") is False


# ─────────────────────────────────────────────
# _es_cif / _es_expediente
# ─────────────────────────────────────────────

def test_es_cif_valido():
    assert _es_cif("G01375344") is True

def test_es_cif_invalido():
    assert _es_cif("Asociación") is False
    assert _es_cif("3.404,35") is False

def test_es_expediente_formato_2025():
    assert _es_expediente("2025B101") is True

def test_es_expediente_texto_normal():
    assert _es_expediente("Gatos Madrid") is False


# ─────────────────────────────────────────────
# mapear_indices
# ─────────────────────────────────────────────

def test_mapear_indices_headers_basicos():
    headers = ["cif", "expediente", "entidad", "puntuación"]
    mapa = mapear_indices(headers)
    assert mapa["cif"] == 0
    assert mapa["expediente"] == 1
    assert mapa["entidad"] == 2

def test_mapear_indices_concedido_entidad_no_es_entidad():
    # Bug histórico: "concedido entidad – euros" se mapeaba como entidad=5
    # sobreescribiendo la columna real (índice 2). Ahora debe ir a importe_idx.
    headers = ["cif", "expediente", "entidad", "línea de actuación", "ptos",
               "concedido entidad – euros"]
    mapa = mapear_indices(headers)
    assert mapa["entidad"] == 2          # columna real preservada
    assert mapa["importe_idx"] == 5      # importe mapeado correctamente

def test_mapear_indices_cuantia_va_a_importe():
    headers = ["expediente", "entidad", "cuantía concedida"]
    mapa = mapear_indices(headers)
    assert mapa.get("importe_idx") == 2
    assert mapa.get("entidad") == 1

def test_mapear_indices_nif_equivale_a_cif():
    headers = ["nif", "expediente", "entidad"]
    mapa = mapear_indices(headers)
    assert mapa["cif"] == 0

def test_mapear_indices_linea_actuacion():
    headers = ["cif", "expediente", "entidad", "línea de actuación", "ptos",
               "concedido entidad – euros"]
    mapa = mapear_indices(headers)
    assert mapa.get("linea") == 3


# ─────────────────────────────────────────────
# normalizar_linea
# ─────────────────────────────────────────────

def test_normalizar_linea_animales_abandonados():
    assert normalizar_linea("LÍNEA ANIMALES ABANDONADOS.") == "animales_abandonados"

def test_normalizar_linea_colonias_felinas():
    assert normalizar_linea("LÍNEA COLONIAS FELINAS.") == "colonias_felinas"

def test_normalizar_linea_texto_parcial():
    assert normalizar_linea("abandon") == "animales_abandonados"
    assert normalizar_linea("felin") == "colonias_felinas"

def test_normalizar_linea_none():
    assert normalizar_linea(None) is None
    assert normalizar_linea("otra cosa") is None


# ─────────────────────────────────────────────
# extraer_entidad_2025
# ─────────────────────────────────────────────

def _celdas(textos):
    """Construye una lista de objetos Tag simulados a partir de strings."""
    soup = BeautifulSoup(
        "".join(f"<td>{t}</td>" for t in textos), "html.parser"
    )
    return soup.find_all("td")


def test_extraer_entidad_indice_correcto():
    celdas = _celdas(["G01375344", "2025B101", "Asociación Gatos Madrid", "LÍNEA ANIMALES", "76,00", "4.011,29"])
    assert extraer_entidad_2025(celdas, 2) == "Asociación Gatos Madrid"

def test_extraer_entidad_fallback_cuando_indice_apunta_a_importe():
    # Simula el bug histórico: índice 5 apunta a "4.011,29" (importe).
    # El fallback debe encontrar el nombre real en el índice 2.
    celdas = _celdas(["G01375344", "2025B101", "Asociación Gatos Madrid", "LÍNEA ANIMALES", "76,00", "4.011,29"])
    resultado = extraer_entidad_2025(celdas, 5)
    assert resultado == "Asociación Gatos Madrid"

def test_extraer_entidad_no_devuelve_cif():
    # Si solo hay CIF y número, devuelve None.
    celdas = _celdas(["G01375344", "2025B101", "4.011,29"])
    resultado = extraer_entidad_2025(celdas, 2)
    assert resultado is None

def test_extraer_entidad_no_devuelve_numero():
    celdas = _celdas(["G01375344", "4.011,29"])
    assert extraer_entidad_2025(celdas, 1) is None


# ─────────────────────────────────────────────
# Detección de estado: ANEXO IV no es concedida
# ─────────────────────────────────────────────

XML_MINIMO = """<?xml version="1.0" encoding="UTF-8"?>
<documento>
<texto>
<p>ANEXO I</p>
<p>Entidades beneficiarias</p>
<table>
  <thead><tr>
    <th>CIF</th><th>Expediente</th><th>Entidad</th>
    <th>Línea de actuación</th><th>Ptos</th><th>Concedido entidad – Euros</th>
  </tr></thead>
  <tbody>
    <tr><td>G00000001</td><td>2025B001</td><td>Protectora Ejemplo</td>
        <td>LÍNEA ANIMALES ABANDONADOS.</td><td>80,00</td><td>5.000,00</td></tr>
  </tbody>
</table>
<p>ANEXO IV</p>
<p>Solicitudes admitidas que no adquieren la condición de beneficiarias al no haber alcanzado la puntuación mínima</p>
<table>
  <thead><tr>
    <th>CIF</th><th>Expediente</th><th>Entidad</th>
    <th>Linea de actuación</th><th>Puntos</th>
  </tr></thead>
  <tbody>
    <tr><td>G00000002</td><td>2025B002</td><td>Colonia Felina Ejemplo</td>
        <td>LÍNEA COLONIAS FELINAS.</td><td>30,00</td></tr>
  </tbody>
</table>
</texto>
</documento>
"""


def test_estado_anexo_iv_es_denegada_no_concedida():
    mock_response = MagicMock()
    mock_response.content = XML_MINIMO.encode("utf-8")

    with patch("scripts.data_extractor.parser_EPAs_BOE_2025.requests.get",
               return_value=mock_response):
        resultados = parsear_boe_epa_2025("http://fake-url")

    concedidas = [r for r in resultados if r["estado"] == "concedida"]
    denegadas  = [r for r in resultados if r["estado"] == "denegada"]

    assert len(concedidas) == 1
    assert concedidas[0]["num_expediente"] == "2025B001"
    assert len(denegadas) == 1
    assert denegadas[0]["num_expediente"] == "2025B002"

def test_linea_extraida_en_concedidas():
    mock_response = MagicMock()
    mock_response.content = XML_MINIMO.encode("utf-8")

    with patch("scripts.data_extractor.parser_EPAs_BOE_2025.requests.get",
               return_value=mock_response):
        resultados = parsear_boe_epa_2025("http://fake-url")

    concedida = next(r for r in resultados if r["estado"] == "concedida")
    assert concedida["linea"] == "animales_abandonados"
    assert concedida["entidad"] == "Protectora Ejemplo"
    assert concedida["importe"] == 5000.0
