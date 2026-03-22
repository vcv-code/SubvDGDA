import os
import json

from scripts.pdf_extraction.parser_eell_base import parsear_eell_base
from scripts.pdf_extraction.parser_eell_2025 import parsear_eell_2025

BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, "../../data/raw/eell")
OUTPUT_DIR = os.path.join(BASE_DIR, "../../data/processed")

def obtener_anio(nombre_archivo):
    if "2023" in nombre_archivo:
        return "2023"
    elif "2024" in nombre_archivo:
        return "2024"
    elif "2025" in nombre_archivo:
        return "2025"
    return "otros"

def procesar_archivo(ruta):
    nombre = os.path.basename(ruta)

    # 🔹 XML (BOE 2025)
    if ruta.lower().endswith(".xml"):
        print(f"Procesando (BOE XML): {nombre}")
        return parsear_eell_2025(ruta)

    # 🔹 PDF 2025 (por si queda alguno)
    elif ruta.lower().endswith(".pdf") and "2025" in nombre:
        print(f"Procesando (2025 PDF): {nombre}")
        return parsear_eell_2025(ruta)

    # 🔹 PDF base (2023–2024)
    elif ruta.lower().endswith(".pdf"):
        print(f"Procesando (base): {nombre}")
        return parsear_eell_base(ruta)

    else:
        print(f"Formato no soportado: {nombre}")
        return []


def main():
    archivos = []

    for root, dirs, files in os.walk(PDF_DIR):
        for file in files:
            if file.lower().endswith((".pdf", ".xml")):
                archivos.append(os.path.join(root, file))

    if not archivos:
        print("No hay archivos en data/raw/eell")
        return

    for archivo in archivos:
        resultados = procesar_archivo(archivo)

        nombre_salida = os.path.basename(archivo)
        nombre_salida = nombre_salida.replace(".pdf", ".json").replace(".xml", ".json")

        anio = obtener_anio(nombre_salida)

        ruta_salida = os.path.join(OUTPUT_DIR, "eell", anio, nombre_salida)

        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"Guardado: {ruta_salida} ({len(resultados)} filas)")


if __name__ == "__main__":
    main()