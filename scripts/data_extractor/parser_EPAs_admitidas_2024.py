"""
parser_EPAs_admitidas_2024.py
=============================
Extrae la LÍNEA DE SUBVENCIÓN (colonias felinas / animales abandonados) de cada
entidad a partir de la "Relación definitiva de solicitudes admitidas y excluidas"
de la convocatoria EPA 2024 (PDF de la Sede Electrónica).

Motivación
----------
El BOE de concesión 2024 no desglosa la línea por entidad, así que en la BD las
concesiones EPA 2024 tienen `linea = NULL`. Este documento (Anexo I, admitidas)
sí trae la columna "Línea de subvención" (SÍ COLONIAS / SÍ OTROS), y el
expediente (2024Bxxx) permite cruzarla con las concesiones ya cargadas.

Diseño
------
Se trabaja sobre el TEXTO del PDF (no extract_tables), acumulando por expediente
todas sus líneas (el nombre de la entidad a veces ocupa dos líneas de celda).
Para cada expediente se ancla el CIF: la línea de subvención es SIEMPRE el texto
que va DESPUÉS del CIF. Esto evita falsos positivos con nombres que contienen la
palabra "COLONIAS" (p. ej. "ASOC COLONIAS GATUNAS", cuya línea real puede ser
otra). Solo se procesa el ANEXO I (admitidas); los anexos II/III/IV se ignoran.

Salida: lista de dicts {num_expediente, cif, linea} y, como script, un CSV en
data/processed/epas/2024/linea_epa_2024.csv.
"""

import csv
import os
import re

import pdfplumber


# =========================
# PATRONES
# =========================

# Expediente EPA: 2024B123 (algún arrastre de 2023, p. ej. 2023B628)
_EXP_RE = re.compile(r"^(20\d{2}B\d{3})\b")

# CIF de entidad: letra + 8 caracteres (7 dígitos + alfanumérico). Se tolera una
# 's' final espuria vista en el origen (p. ej. "G67946921s").
_CIF_RE = re.compile(r"\b([A-Z]\d{7}[A-Z0-9])s?\b")

# Encabezados de anexo, del más largo al más corto para no solaparse.
_SECCION_PATRONES = [
    (re.compile(r"\bANEXO\s+IV\b",           re.IGNORECASE), "desistidas"),
    (re.compile(r"\bANEXO\s+III\b",          re.IGNORECASE), "causas"),
    (re.compile(r"\bANEXO\s+II\b(?!\s*I)",   re.IGNORECASE), "excluidas"),
    (re.compile(r"\bANEXO\s+I\b(?!\s*[IV])", re.IGNORECASE), "admitidas"),
]

# Líneas de cabecera/pie que no son datos y no deben contaminar el buffer.
_RUIDO_RE = re.compile(
    r"^(Código seguro|CSV\s*:|DIRECCIÓN DE|FIRMANTE|MINISTERIO|SECRETARÍA|"
    r"DIRECCIÓN GENERAL|CORREO ELECTR|DIRECCIÓN POSTAL|Paseo del Prado|"
    r"28071|Página\b|Expediente\b|SOLICITUDES ADMITIDAS|Y AGENDA)",
    re.IGNORECASE,
)


def detectar_seccion(linea):
    for patron, seccion in _SECCION_PATRONES:
        if patron.search(linea):
            return seccion
    return None


def normalizar_linea(texto):
    """
    Mapea el texto de la columna "Línea de subvención" al enum de la BD.
    Solo debe recibir el texto que va DESPUÉS del CIF.
    Variantes vistas: 'SÍ COLONIAS', 'SÍ OTROS', 'COLONIAS', 'SI COLONIAS',
    'No aplica'. Devuelve None para "No aplica" o texto no reconocido.
    """
    t = (texto or "").upper()
    if "COLONIA" in t:
        return "colonias_felinas"
    if "OTROS" in t:
        return "animales_abandonados"
    return None


# =========================
# PARSER
# =========================

def _parsear_buffer(exp, buffer_texto):
    """Ancla el CIF en el buffer del expediente; la línea es lo que va después."""
    buffer_texto = re.sub(r"\s+", " ", buffer_texto).strip()
    m = _CIF_RE.search(buffer_texto)
    cif = m.group(1) if m else None
    linea_txt = buffer_texto[m.end():] if m else ""
    return {
        "num_expediente": exp,
        "cif":            cif,
        "linea":          normalizar_linea(linea_txt),
    }


def parsear_admitidas_epa2024(ruta_pdf):
    """
    Devuelve una lista de dicts {num_expediente, cif, linea} para todas las
    entidades del ANEXO I (admitidas). Solo procesa esa sección.
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        lineas = []
        for pagina in pdf.pages:
            for l in (pagina.extract_text() or "").split("\n"):
                lineas.append(l.strip())

    registros = []
    orden = {}          # exp -> índice en registros (dedup, primera aparición)
    seccion = None
    exp_actual = None
    buffer = []

    def _volcar():
        if exp_actual and exp_actual not in orden:
            orden[exp_actual] = len(registros)
            registros.append(_parsear_buffer(exp_actual, " ".join(buffer)))

    for linea in lineas:
        if not linea:
            continue

        nueva = detectar_seccion(linea)
        if nueva is not None:
            _volcar()
            exp_actual = None
            buffer = []
            seccion = nueva
            continue

        if seccion != "admitidas":
            continue

        if _RUIDO_RE.search(linea):
            continue

        m = _EXP_RE.match(linea)
        if m:
            _volcar()                 # cierra el expediente anterior
            exp_actual = m.group(1)
            buffer = [linea[m.end():]]
        elif exp_actual:
            buffer.append(linea)      # continuación (nombre en 2ª línea, etc.)

    _volcar()                          # último expediente
    return registros


# =========================
# SCRIPT
# =========================

_RUTA_PDF = "data/raw/epas/2024/relacion-def-admitidas-EPA2024.pdf"
_RUTA_CSV = "data/processed/epas/2024/linea_epa_2024.csv"


def main():
    registros = parsear_admitidas_epa2024(_RUTA_PDF)
    os.makedirs(os.path.dirname(_RUTA_CSV), exist_ok=True)
    with open(_RUTA_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["num_expediente", "cif", "linea"])
        w.writeheader()
        for r in registros:
            w.writerow(r)

    con_linea = sum(1 for r in registros if r["linea"])
    print(f"Admitidas EPA 2024 parseadas: {len(registros)}")
    print(f"  con línea: {con_linea}  ·  sin línea (No aplica/desconocida): {len(registros) - con_linea}")
    print(f"CSV escrito en: {_RUTA_CSV}")


if __name__ == "__main__":
    main()
