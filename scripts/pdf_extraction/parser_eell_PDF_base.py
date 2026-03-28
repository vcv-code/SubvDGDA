"""
parser_eell_PDF_base.py
=======================
Parser para resoluciones definitivas EELL en formato PDF (2023, 2024).

Estructura estándar del BOE:
  ANEXO I   — Entidades beneficiarias   (expediente, entidad, CIF, puntuación, importe, ...)
  ANEXO II  — Solicitudes desestimadas  (expediente, entidad, CIF, puntuación, ...)
  ANEXO III — Solicitudes excluidas     (expediente, entidad, CIF, causa exclusión)
  ANEXO IV  — Solicitudes desistidas    (expediente, entidad, CIF[, causa])

DISEÑO (dos pasadas):
  Pasada 1 — TEXT (estado correcto por expediente):
    Recorre el texto página a línea para asignar el estado exacto a cada expediente.
    Al ir línea a línea detecta la transición de sección dentro de la misma página,
    evitando la clasificación errónea en páginas mixtas (fin de ANEXO II + inicio III).

  Pasada 2 — TABLAS (datos completos):
    Usa extract_tables() de pdfplumber para extraer todos los campos, incluidas las
    entidades con nombres que ocupan varias líneas de celda (habitual en 2023).
    Para cada fila válida usa el estado ya calculado en la pasada 1.
    Override: si el importe > 0 siempre es "concedida" (gestiona cualquier residuo).
"""

import os
import re

import pdfplumber


# =========================
# UTILIDADES
# =========================

def limpiar_texto(valor):
    if not valor:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def limpiar_importe(texto):
    """Convierte importe europeo a float. Devuelve 0.0 si no válido o < 100."""
    if not texto:
        return 0.0
    texto = re.sub(r"\s+", "", str(texto)).replace("€", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")
    try:
        valor = float(texto)
        return valor if valor >= 100 else 0.0
    except:
        return 0.0


def limpiar_puntos(texto):
    if not texto:
        return None
    try:
        return float(re.sub(r"\s+", "", str(texto)).replace(",", "."))
    except:
        return None


# =========================
# DETECCIÓN DE SECCIÓN
# =========================

# Orden de evaluación: del más largo al más corto para evitar solapamientos
_SECCION_PATRONES = [
    (re.compile(r"^ANEXO\s+IV\b",            re.IGNORECASE), "desistida"),
    (re.compile(r"^ANEXO\s+III\b",           re.IGNORECASE), "excluida"),
    (re.compile(r"^ANEXO\s+II\b(?!\s*I)",    re.IGNORECASE), "no_beneficiaria"),
    (re.compile(r"^ANEXO\s+I\b(?!\s*[IV])",  re.IGNORECASE), "concedida"),
]

def detectar_seccion(linea):
    """Devuelve el nuevo estado si la línea es un encabezado de ANEXO, o None."""
    for patron, estado in _SECCION_PATRONES:
        if patron.match(linea.strip()):
            return estado
    return None


# =========================
# CIF
# =========================

_CIF_RE = re.compile(r"^[A-Z]\d{7}[A-Z0-9]$")
_EXP_RE = re.compile(r"^EXP\d{4}/")

def buscar_cif_en_fila(fila):
    """Devuelve (índice, cif) de la primera celda que coincide con patrón CIF."""
    for i, celda in enumerate(fila):
        if celda and _CIF_RE.match(celda.strip()):
            return i, celda.strip()
    return None, None


# =========================
# PASADA 1: ESTADO POR EXPEDIENTE (desde texto)
# =========================

def _pasada_texto(pdf):
    """
    Recorre el texto línea a línea y devuelve un dict {expediente → estado}.
    Al procesar línea a línea dentro de cada página, la transición de sección
    se asigna correctamente incluso en páginas mixtas.
    """
    exp_estado = {}
    estado_actual = None

    for pagina in pdf.pages:
        texto = pagina.extract_text() or ""
        for linea in texto.split("\n"):
            linea = linea.strip()
            if not linea:
                continue

            # ¿Encabezado de sección?
            nuevo = detectar_seccion(linea)
            if nuevo is not None:
                estado_actual = nuevo
                continue

            if estado_actual is None:
                continue

            # ¿Línea con expediente?
            if linea.startswith("EXP"):
                exp = linea.split()[0]
                if _EXP_RE.match(exp) and exp not in exp_estado:
                    exp_estado[exp] = estado_actual

    return exp_estado


# =========================
# PASADA 2: DATOS COMPLETOS (desde tablas)
# =========================

def _parsear_fila_tabla(fila, estado):
    """
    Extrae los campos de una fila de extract_tables() usando el estado ya conocido.
    CIF se busca en todas las columnas (no asume posición fija).
    """
    if not fila:
        return None

    fila = [limpiar_texto(c) for c in fila]

    # Columna 0: expediente
    expediente = fila[0]
    if not expediente or not _EXP_RE.match(expediente):
        return None

    # Buscar CIF
    idx_cif = None
    cif = None
    for i, celda in enumerate(fila):
        if celda and _CIF_RE.match(celda):
            idx_cif, cif = i, celda
            break

    if idx_cif is None:
        return None

    # Entidad: columnas entre expediente y CIF
    entidad = " ".join(
        fila[i] for i in range(1, idx_cif) if fila[i]
    ).strip() or None

    # Columnas útiles tras el CIF
    resto = [c for c in fila[idx_cif + 1:] if c]

    # Buscar importe en el resto (número europeo grande)
    importe = 0.0
    for col in resto:
        candidato = limpiar_importe(col)
        if candidato > 0:
            importe = candidato
            break

    # Override: importe > 0 → siempre concedida
    if importe > 0:
        estado = "concedida"

    # Campos según estado
    puntos = None
    causa_exclusion = None

    if estado in ("concedida", "no_beneficiaria"):
        puntos = limpiar_puntos(resto[0]) if resto else None

    elif estado == "excluida":
        # Primer campo no numérico o numérico (código de causa)
        causa_exclusion = resto[0] if resto else None

    # desistida: sin campos extra

    return {
        "num_expediente":  expediente,
        "entidad":         entidad,
        "cif":             cif,
        "puntos":          puntos,
        "importe":         importe,
        "causa_exclusion": causa_exclusion,
        "estado":          estado,
    }


# =========================
# PARSER PRINCIPAL
# =========================

def parsear_eell_base(ruta_pdf):
    """
    Parser genérico para resoluciones definitivas EELL en PDF (2023, 2024).

    Pasada 1 (texto): asigna el estado correcto a cada expediente, respetando
    las transiciones de sección dentro de páginas mixtas.

    Pasada 2 (tablas): extrae datos completos (incluyendo entidades multilínea)
    usando el estado calculado en la pasada 1.

    Devuelve lista de dicts: num_expediente, entidad, cif, puntos, importe,
    causa_exclusion, estado, _meta.
    """
    resultados = []
    vistos = set()

    with pdfplumber.open(ruta_pdf) as pdf:

        # --- Pasada 1: estado por expediente ---
        exp_estado = _pasada_texto(pdf)

        # --- Pasada 2: datos completos desde tablas ---
        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            tablas = pagina.extract_tables()
            for tabla in tablas:
                if not tabla:
                    continue
                for fila in tabla:
                    if not fila or not fila[0]:
                        continue

                    exp = limpiar_texto(fila[0])
                    if not _EXP_RE.match(exp):
                        continue

                    # Obtener estado de la pasada 1
                    estado = exp_estado.get(exp)
                    if estado is None:
                        continue

                    # Dedup
                    if exp in vistos:
                        continue

                    datos = _parsear_fila_tabla(fila, estado)
                    if datos is None:
                        continue

                    vistos.add(exp)
                    datos["_meta"] = {
                        "pagina": num_pagina,
                        "pdf":    os.path.basename(ruta_pdf),
                    }
                    resultados.append(datos)

        # --- Pasada 3 (fallback): expedientes en texto que no aparecen en tablas ---
        # Ocurre raramente cuando pdfplumber no detecta la fila como parte de una tabla.
        pendientes = {exp: est for exp, est in exp_estado.items() if exp not in vistos}
        if pendientes:
            for num_pagina, pagina in enumerate(pdf.pages, start=1):
                for linea in (pagina.extract_text() or "").split("\n"):
                    linea = linea.strip()
                    if not linea.startswith("EXP"):
                        continue
                    exp = linea.split()[0]
                    if exp not in pendientes:
                        continue
                    estado = pendientes[exp]

                    # Extraer CIF de la línea
                    m_cif = re.search(r"\b([A-Z]\d{7}[A-Z0-9])\b", linea)
                    if not m_cif:
                        continue

                    cif = m_cif.group(1)
                    parte_ant = linea[:m_cif.start()].strip()
                    parte_post = linea[m_cif.end():].strip()

                    # Entidad entre EXP y CIF
                    espacio = parte_ant.find(" ")
                    entidad = parte_ant[espacio:].strip() if espacio != -1 else None

                    # Puntuación / importe en la parte posterior
                    tokens = parte_post.split()
                    importe = 0.0
                    puntos = None
                    causa_exclusion = None
                    for tok in tokens:
                        candidato = limpiar_importe(tok)
                        if candidato > 0:
                            importe = candidato
                    if importe > 0:
                        estado = "concedida"
                    if estado in ("concedida", "no_beneficiaria") and tokens:
                        puntos = limpiar_puntos(tokens[0])
                    elif estado == "excluida" and tokens:
                        causa_exclusion = tokens[0]

                    vistos.add(exp)
                    resultados.append({
                        "num_expediente":  exp,
                        "entidad":         entidad or None,
                        "cif":             cif,
                        "puntos":          puntos,
                        "importe":         importe,
                        "causa_exclusion": causa_exclusion,
                        "estado":          estado,
                        "_meta": {"pagina": num_pagina, "pdf": os.path.basename(ruta_pdf)},
                    })

    return resultados
