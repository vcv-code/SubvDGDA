"""
parser_eell_BOE_2025.py
=======================
Parser para la resolución definitiva EELL 2025 (BOE-A-2025-27204).

Estructura del BOE:
  ANEXO I  — Puntuaciones (tabla XML, ~1010 expedientes)
  ANEXO II — Beneficiarias (imágenes PNG, NO parseable desde XML)
  ANEXO III — Excluidas (tabla XML, expediente en columna 1)
  ANEXO IV  — Desistidas (tabla XML, expediente en columna 1)
  ANEXO V   — No beneficiarias (tabla XML, expediente en columna 1)

Estrategia:
  1. Base de datos: eell_2025.xlsx (mismo directorio que el XML).
     Contiene los 991 expedientes evaluados con puntos e importe.
  2. Importes y tramos definitivos: eell_2025_beneficiarias.xlsx
     (también en el mismo directorio). Contiene los 40 beneficiarios
     con sus importes correctos extraídos manualmente del ANEXO II
     (imágenes). Sobreescribe los importes del xlsx base, que en
     algunos casos (p.ej. agrupaciones) pueden aparecer como 0.
  3. Estado se asigna leyendo los ANEXOS IV y V del XML:
     - ANEXO IV → "desistida"
     - ANEXO V  → "no_beneficiaria"
     - El resto  → "concedida"
  4. Los excluidos (ANEXO III) no están en el xlsx y se ignoran
     para mantener la cifra de 991 registros esperada.
"""

import json
import os
import re
from collections import Counter

from bs4 import BeautifulSoup


# =========================
# UTILIDADES
# =========================

def limpiar_texto(texto):
    if not texto:
        return None
    return texto.strip() or None


# =========================
# LECTOR DE XLSX
# =========================

def cargar_xlsx(ruta_xlsx):
    """
    Carga los 991 registros evaluados desde el Excel de referencia.
    Devuelve un dict: expediente → {cif, entidad, puntos, importe}.
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl es necesario: pip install openpyxl --break-system-packages")

    wb = openpyxl.load_workbook(ruta_xlsx)
    ws = wb.active

    registros = {}
    for fila in ws.iter_rows(min_row=2, values_only=True):
        exp, nif, entidad, puntos, importe = fila[0], fila[1], fila[2], fila[3], fila[4]
        if not exp:
            continue
        registros[str(exp).strip()] = {
            "cif":     str(nif).strip() if nif else None,
            "entidad": str(entidad).strip() if entidad else None,
            "puntos":  float(puntos) if puntos is not None else None,
            "importe": float(importe) if importe else 0.0,
        }

    return registros


def cargar_beneficiarias_xlsx(ruta_xlsx):
    """
    Carga los 40 beneficiarios definitivos desde eell_2025_beneficiarias.xlsx.

    Lee dos hojas:
      - 'Entidades_beneficiarias': tramo, NIF, expediente, entidad, importe,
        ¿agrupación?, nº municipios
      - 'Municipios': tramo, NIF municipio, nombre municipio, expediente
        representante, nombre representante, importe asignado

    Devuelve un dict: expediente → {tramo, importe, es_agrupacion,
                                     municipios_agrupacion}
      - es_agrupacion: bool
      - municipios_agrupacion: lista de {cif, nombre, importe_asignado}
        Solo se rellena cuando es_agrupacion=True; None en caso contrario.
        Incluye el ayuntamiento representante como primer miembro.
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl es necesario: pip install openpyxl --break-system-packages")

    wb = openpyxl.load_workbook(ruta_xlsx)

    # --- Hoja Entidades_beneficiarias ---
    # Fila 1: título; fila 2: cabeceras; datos desde fila 3
    ws_benef = wb["Entidades_beneficiarias"]
    beneficiarias = {}
    for fila in ws_benef.iter_rows(min_row=3, values_only=True):
        tramo, nif, exp, entidad, importe, agrupacion, num_mun = (
            fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6]
        )
        if not exp or not isinstance(tramo, int):
            continue
        exp_str = str(exp).strip()
        es_agrup = str(agrupacion).strip().lower() in ("sí", "si", "yes", "true") if agrupacion else False
        beneficiarias[exp_str] = {
            "tramo":               int(tramo),
            "importe":             float(importe) if importe else 0.0,
            "es_agrupacion":       es_agrup,
            "municipios_agrupacion": None,  # se rellena abajo desde hoja Municipios
        }

    # --- Hoja Municipios ---
    # Fila 1: título; fila 2: cabeceras; datos desde fila 3
    # Columnas: tramo, NIF municipio, nombre municipio, exp representante,
    #           nombre representante, importe asignado
    ws_mun = wb["Municipios"]
    muns_por_exp = {}
    for fila in ws_mun.iter_rows(min_row=3, values_only=True):
        tramo, nif_mun, nombre_mun, exp_rep, nombre_rep, imp_mun = (
            fila[0], fila[1], fila[2], fila[3], fila[4], fila[5]
        )
        if not exp_rep or not isinstance(tramo, int):
            continue
        exp_str = str(exp_rep).strip()
        muns_por_exp.setdefault(exp_str, []).append({
            "cif":             str(nif_mun).strip() if nif_mun else None,
            "nombre":          str(nombre_mun).strip() if nombre_mun else None,
            "importe_asignado": float(imp_mun) if imp_mun else 0.0,
        })

    # Adjuntar municipios solo a las agrupaciones
    for exp_str, benef in beneficiarias.items():
        if benef["es_agrupacion"]:
            benef["municipios_agrupacion"] = muns_por_exp.get(exp_str)

    return beneficiarias


# =========================
# LECTOR DE ANEXOS XML
# =========================

def leer_expedientes_anexo(soup, num_anexo):
    """
    Extrae el conjunto de expedientes de un ANEXO específico del XML.
    En ANEXO III, IV y V el expediente está en la columna 1 (no en la 0).
    Devuelve un set de strings de expediente.
    """
    elementos = soup.find_all(["p", "table"])
    en_anexo = False
    expedientes = set()

    patron = re.compile(rf'^ANEXO\s+{num_anexo}\b', re.IGNORECASE)

    for el in elementos:
        if el.name == "p":
            texto = el.get_text(" ", strip=True)
            if patron.match(texto.strip()):
                en_anexo = True
            elif en_anexo and re.match(r'^ANEXO\s+[IVX]+\b', texto.strip(), re.IGNORECASE):
                break  # siguiente anexo, paramos

        elif el.name == "table" and en_anexo:
            for fila in el.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) < 2:
                    continue
                # Expediente en columna 1 para ANEXO III, IV, V
                exp = celdas[1].get_text(strip=True)
                if exp.startswith("EXP"):   # acepta EXP2025/ y EXP/NNNNN
                    expedientes.add(exp)

    return expedientes


def leer_filas_anexo_iii(soup):
    """
    Lee las filas completas del ANEXO III (excluidas) del XML de 2025.
    Columnas: col0=NIF, col1=expediente, col2=entidad, col3=causa_exclusion

    Devuelve un dict: expediente → {cif, entidad, causa_exclusion}
    """
    elementos = soup.find_all(["p", "table"])
    en_anexo = False
    filas = {}

    for el in elementos:
        if el.name == "p":
            texto = el.get_text(" ", strip=True)
            if re.match(r'^ANEXO\s+III\b', texto.strip(), re.IGNORECASE):
                en_anexo = True
            elif en_anexo and re.match(r'^ANEXO\s+[IVX]+\b', texto.strip(), re.IGNORECASE):
                break

        elif el.name == "table" and en_anexo:
            for fila in el.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) < 2:
                    continue
                cif  = celdas[0].get_text(strip=True)
                exp  = celdas[1].get_text(strip=True)
                ent  = celdas[2].get_text(strip=True) if len(celdas) > 2 else None
                causa = celdas[3].get_text(strip=True) if len(celdas) > 3 else None
                if exp.startswith("EXP"):
                    filas[exp] = {
                        "cif":            cif or None,
                        "entidad":        ent or None,
                        "causa_exclusion": causa or None,
                    }

    return filas


def _leer_tabla_anexo_v(soup):
    """
    Lee la tabla completa del ANEXO V (no beneficiarias) del XML.
    Columnas: col0=NIF, col1=expediente, col2=entidad, col3=tramo,
              col4=cofinanciación, col5=actuaciones, col6=puntos
    Devuelve dict: expediente → {cif, entidad, puntos}
    """
    elementos = soup.find_all(["p", "table"])
    en_anexo = False
    filas = {}

    for el in elementos:
        if el.name == "p":
            texto = el.get_text(" ", strip=True)
            if re.match(r'^ANEXO\s+V\b', texto.strip(), re.IGNORECASE):
                en_anexo = True
            elif en_anexo and re.match(r'^ANEXO\s+[IVX]+\b', texto.strip(), re.IGNORECASE):
                break

        elif el.name == "table" and en_anexo:
            for fila in el.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) < 3:
                    continue
                cif     = celdas[0].get_text(strip=True) or None
                exp     = celdas[1].get_text(strip=True)
                entidad = celdas[2].get_text(strip=True) or None
                try:
                    puntos = float(celdas[6].get_text(strip=True).replace(",", ".")) if len(celdas) > 6 else None
                except ValueError:
                    puntos = None
                if exp.startswith("EXP"):
                    filas[exp] = {"cif": cif, "entidad": entidad, "puntos": puntos}

    return filas


# =========================
# PARSER PRINCIPAL
# =========================

def parsear_eell_2025(ruta_xml):
    """
    Combina el xlsx de referencia (base) con los estados de los anexos XML
    y los importes/tramos del xlsx de beneficiarias.

    Resultado: 991 registros con estado, importe y tramo correctos.
    """

    # Buscar xlsx en el mismo directorio que el XML
    dir_xml = os.path.dirname(os.path.abspath(ruta_xml))
    ruta_xlsx = os.path.join(dir_xml, "eell_2025.xlsx")
    ruta_benef = os.path.join(dir_xml, "eell_2025_beneficiarias.xlsx")

    if not os.path.exists(ruta_xlsx):
        raise FileNotFoundError(
            f"No se encontró eell_2025.xlsx en {dir_xml}. "
            "Es necesario para el parser EELL 2025."
        )

    # --- 1. Cargar base desde xlsx ---
    base = cargar_xlsx(ruta_xlsx)
    print(f"[EELL BOE 2025] Xlsx base cargado: {len(base)} expedientes")

    # --- 2. Cargar importes, tramos, agrupaciones y municipios desde beneficiarias xlsx ---
    beneficiarias = {}
    if os.path.exists(ruta_benef):
        beneficiarias = cargar_beneficiarias_xlsx(ruta_benef)
        n_agrup = sum(1 for b in beneficiarias.values() if b["es_agrupacion"])
        print(f"[EELL BOE 2025] Xlsx beneficiarias cargado: {len(beneficiarias)} entidades "
              f"({n_agrup} agrupaciones)")
        # Aplicar sobreescritura de importes en la base
        sobreescritos = 0
        for exp, benef_datos in beneficiarias.items():
            if exp in base:
                importe_base = base[exp]["importe"]
                importe_benef = benef_datos["importe"]
                if importe_base != importe_benef:
                    base[exp]["importe"] = importe_benef
                    sobreescritos += 1
        if sobreescritos:
            print(f"  Importes corregidos desde beneficiarias.xlsx: {sobreescritos}")
    else:
        print(f"[EELL BOE 2025] AVISO: no se encontró {ruta_benef}. "
              "Los importes proceden solo del xlsx base.")

    # --- 3. Leer estados de los anexos XML ---
    with open(ruta_xml, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    excluidas_xml = leer_filas_anexo_iii(soup)   # dict exp → {cif, entidad, causa}
    desistidas    = leer_expedientes_anexo(soup, "IV")
    no_benef_xml  = leer_expedientes_anexo(soup, "V")

    print(f"  Excluidas   (ANEXO III): {len(excluidas_xml)}")
    print(f"  Desistidas  (ANEXO IV):  {len(desistidas)}")
    print(f"  No benef.   (ANEXO V):   {len(no_benef_xml)}")

    # --- 4. Asignar estados y tramos (base: 991 evaluadas) ---
    resultados = []
    for exp, datos in base.items():
        if exp in desistidas:
            estado = "desistida"
        elif exp in no_benef_xml:
            estado = "no_beneficiaria"
        else:
            estado = "concedida"

        # Tramo, agrupacion y municipios: solo para beneficiarias (concedidas)
        tramo = None
        es_agrupacion = False
        municipios_agrupacion = None
        if estado == "concedida" and exp in beneficiarias:
            benef = beneficiarias[exp]
            tramo             = benef["tramo"]
            es_agrupacion     = benef["es_agrupacion"]
            municipios_agrupacion = benef["municipios_agrupacion"]

        resultados.append({
            "num_expediente":       exp,
            "cif":                  datos["cif"],
            "entidad":              datos["entidad"],
            "puntos":               datos["puntos"],
            "importe":              datos["importe"],
            "tramo":                tramo,
            "causa_exclusion":      None,
            "estado":               estado,
            "es_agrupacion":        es_agrupacion,
            "municipios_agrupacion": municipios_agrupacion,
        })

    # --- 5. Añadir las excluidas del ANEXO III (no están en la base xlsx) ---
    for exp, excl in excluidas_xml.items():
        resultados.append({
            "num_expediente":        exp,
            "cif":                   excl["cif"],
            "entidad":               excl["entidad"],
            "puntos":                None,
            "importe":               0.0,
            "tramo":                 None,
            "causa_exclusion":       excl["causa_exclusion"],
            "estado":                "excluida",
            "es_agrupacion":         False,
            "municipios_agrupacion": None,
        })

    # --- 6. Añadir no_beneficiarias del ANEXO V que no están en el xlsx base ---
    # El BOE incluye entidades con formato EXP/NNNNN que no figuran en el xlsx
    # de evaluación (991 registros). Se añaden directamente desde la tabla XML.
    tabla_v = _leer_tabla_anexo_v(soup)
    exps_ya_incluidos = {r["num_expediente"] for r in resultados}
    extra_no_benef = 0
    for exp, datos in tabla_v.items():
        if exp not in exps_ya_incluidos:
            resultados.append({
                "num_expediente":        exp,
                "cif":                   datos["cif"],
                "entidad":               datos["entidad"],
                "puntos":                datos["puntos"],
                "importe":               0.0,
                "tramo":                 None,
                "causa_exclusion":       None,
                "estado":                "no_beneficiaria",
                "es_agrupacion":         False,
                "municipios_agrupacion": None,
            })
            extra_no_benef += 1
    if extra_no_benef:
        print(f"  No benef. extra (fuera de xlsx base): {extra_no_benef}")

    print(f"[EELL BOE 2025] Registros totales: {len(resultados)}")
    print(f"  Estados: {dict(Counter(r['estado'] for r in resultados))}")

    return resultados


def guardar_json(resultados, ruta_xml):
    output = os.path.join(
        os.path.dirname(ruta_xml).replace("raw", "processed"),
        "eell_2025_completo.json"
    )
    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"JSON guardado en: {output}")


if __name__ == "__main__":
    ruta = "data/raw/eell/2025/BOE-A-2025-27204.xml"
    resultados = parsear_eell_2025(ruta)
    guardar_json(resultados, ruta)
