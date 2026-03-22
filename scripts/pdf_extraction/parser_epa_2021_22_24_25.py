import os
from parser_epa_base import extraer_tablas_pdf, guardar_resultados

# --- RUTAS ---
BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, "../../data/raw/epas")


def es_pdf_valido(nombre):
    """
    Asegura que solo procesamos PDFs
    """
    return nombre.lower().endswith(".pdf")


def main():
    if not os.path.exists(PDF_DIR):
        print("❌ No existe la carpeta data/raw/epas")
        return

    # recorrer carpetas por año
    for year in sorted(os.listdir(PDF_DIR)):
        year_path = os.path.join(PDF_DIR, year)

        if not os.path.isdir(year_path):
            continue

        print(f"\n📂 Procesando año: {year}")

        pdfs = [f for f in os.listdir(year_path) if es_pdf_valido(f)]

        if not pdfs:
            print(f"⚠️ No hay PDFs en {year}")
            continue

        for nombre_pdf in pdfs:
            ruta_pdf = os.path.join(year_path, nombre_pdf)

            # importante: incluir año en el nombre
            nombre_base = f"{year}_{os.path.splitext(nombre_pdf)[0]}"

            print(f"   → Procesando {nombre_pdf}")

            try:
                resultados = extraer_tablas_pdf(ruta_pdf)
                guardar_resultados(resultados, nombre_base)

            except Exception as e:
                print(f"❌ Error en {nombre_pdf}: {e}")

    print("\n✅ Procesamiento completado")


if __name__ == "__main__":
    main()