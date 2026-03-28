import os
import json
from collections import Counter

# EELL
from scripts.pdf_extraction.parser_eell_PDF_base import parsear_eell_base
from scripts.pdf_extraction.parser_eell_BOE_2025 import parsear_eell_2025

# EPAs
from scripts.pdf_extraction.parser_EPAs_BOE_base import parsear_boe_epa_base
from scripts.pdf_extraction.parser_EPAs_BOE_2025 import parsear_boe_epa_2025


BASE_DIR = os.path.dirname(__file__)

PDF_DIR = os.path.join(BASE_DIR, "../../data/raw/eell")
OUTPUT_DIR = os.path.join(BASE_DIR, "../../data/processed")


# =========================
# UTILIDADES
# =========================

def obtener_anio(nombre_archivo):
    if "2021" in nombre_archivo:
        return "2021"
    elif "2022" in nombre_archivo:
        return "2022"
    elif "2023" in nombre_archivo:
        return "2023"
    elif "2024" in nombre_archivo:
        return "2024"
    elif "2025" in nombre_archivo:
        return "2025"
    return "otros"


def mostrar_estadisticas(datos):
    total = len(datos)

    estados = Counter(d["estado"] for d in datos if d.get("estado"))
    con_importe = sum(1 for d in datos if d.get("importe") is not None)
    con_puntuacion = sum(1 for d in datos if d.get("puntuacion") is not None)

    print("\n--- RESUMEN ---")
    print(f"Total registros: {total}")

    print("\nEstados:")
    for estado, count in estados.items():
        print(f"  {estado}: {count}")

    print("\nCalidad:")
    print(f"  Con importe: {con_importe}")
    print(f"  Con puntuación: {con_puntuacion}")

    print("----------------\n")


# =========================
# EELL
# =========================

def procesar_archivo_eell(ruta):
    nombre = os.path.basename(ruta)

    if ruta.lower().endswith(".xml"):
        print(f"Procesando EELL (BOE XML): {nombre}")
        return parsear_eell_2025(ruta)

    elif ruta.lower().endswith(".pdf") and "2025" in nombre:
        print(f"Procesando EELL (2025 PDF): {nombre}")
        return parsear_eell_2025(ruta)

    elif ruta.lower().endswith(".pdf"):
        print(f"Procesando EELL (base): {nombre}")
        return parsear_eell_base(ruta)

    else:
        print(f"Formato no soportado: {nombre}")
        return []


# =========================
# MAIN
# =========================

def main():

    # =========================
    # EPAs (SOLO URLs)
    # =========================

    urls_epa = {
        2021: "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-602",
        2022: "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-22122",
        2023: "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-23529",
        2024: "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-23749",
        2025: "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2025-27109"
    }

    for anio, url in urls_epa.items():

        print(f"Procesando EPA {anio}...")

        if anio == 2025:
            resultados = parsear_boe_epa_2025(url)
        else:
            resultados = parsear_boe_epa_base(url, anio)

        mostrar_estadisticas(resultados)

        ruta_salida = os.path.join(OUTPUT_DIR, "epas", str(anio), f"epas_{anio}.json")
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"Guardado EPAs: {ruta_salida} ({len(resultados)} filas)")


    # =========================
    # EELL (SOLO ARCHIVOS)
    # =========================

    archivos_eell = []

    for root, dirs, files in os.walk(PDF_DIR):
        for file in files:
            if file.lower().endswith((".pdf", ".xml")):
                archivos_eell.append(os.path.join(root, file))

    if not archivos_eell:
        print("No hay archivos en data/raw/eell")
        return

    for archivo in archivos_eell:

        resultados = procesar_archivo_eell(archivo)

        mostrar_estadisticas(resultados)

        nombre_salida = os.path.basename(archivo)
        nombre_salida = nombre_salida.replace(".pdf", ".json").replace(".xml", ".json")

        # El parser EELL 2025 combina XML + xlsx; el unificador espera este nombre.
        if "BOE-A-2025-27204" in nombre_salida:
            nombre_salida = "eell_2025_completo.json"

        anio = obtener_anio(nombre_salida)

        ruta_salida = os.path.join(OUTPUT_DIR, "eell", anio, nombre_salida)
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"Guardado EELL: {ruta_salida} ({len(resultados)} filas)")


if __name__ == "__main__":
    main()