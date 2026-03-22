import pdfplumber
import os
import json
import re

# --- RUTAS ---
BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, "../../data/raw/epas/2023")
OUTPUT_DIR = os.path.join(BASE_DIR, "../../data/processed")


def limpiar_texto(texto):
    if not texto:
        return ""
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def parsear_importe(valor):
    if not valor:
        return None
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return None


def detectar_anexo(texto):
    texto = texto.upper()

    if "ADQUIEREN LA CONDICI" in texto:
        return "beneficiarias"
    elif "NO ADQUIEREN LA CONDICI" in texto:
        return "admitidas_no_beneficiarias"
    elif "SOLICITUDES EXCLUIDAS" in texto:
        return "excluidas"
    elif "SOLICITUDES DESISTIDAS" in texto:
        return "desistidas"

    return None


def es_expediente(linea):
    return bool(re.search(r"\d{4}[A-Z]\d+", linea))


def extraer_datos_linea(linea):
    """
    Intenta extraer:
    expediente | CIF | entidad | puntos | importe
    """

    # dividir por espacios múltiples
    partes = re.split(r"\s{2,}", linea)

    if len(partes) < 3:
        return None

    expediente = partes[0].strip()
    cif = partes[1].strip()

    entidad = partes[2].strip()

    puntos = None
    importe = None

    if len(partes) >= 4:
        match_puntos = re.search(r"\d+([.,]\d+)?", partes[3])
        if match_puntos:
            puntos = float(match_puntos.group(0).replace(",", "."))

    if len(partes) >= 5:
        importe = parsear_importe(partes[4])

    return {
        "num_expediente": expediente,
        "cif": cif,
        "entidad": limpiar_texto(entidad),
        "puntos": puntos,
        "importe": importe
    }


def procesar_pdf(ruta_pdf):
    resultados = {
        "beneficiarias": [],
        "admitidas_no_beneficiarias": [],
        "excluidas": [],
        "desistidas": []
    }

    anexo_actual = None

    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""

            anexo_detectado = detectar_anexo(texto)
            if anexo_detectado:
                anexo_actual = anexo_detectado

            if not anexo_actual:
                continue

            lineas = texto.split("\n")

            for linea in lineas:
                linea = linea.strip()

                if not linea:
                    continue

                if not es_expediente(linea):
                    continue

                datos = extraer_datos_linea(linea)

                if not datos:
                    continue

                resultados[anexo_actual].append(datos)

    return resultados


def guardar_resultados(resultados, nombre_base):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for anexo, datos in resultados.items():
        if not datos:
            continue

        datos = sorted(datos, key=lambda x: x["num_expediente"])

        nombre_archivo = f"{nombre_base}_{anexo}.json"
        ruta = os.path.join(OUTPUT_DIR, nombre_archivo)

        if os.path.exists(ruta):
            os.remove(ruta)

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        print(f"Guardado: {nombre_archivo} ({len(datos)} filas)")


def main():
    if not os.path.exists(PDF_DIR):
        print("❌ No existe carpeta 2023")
        return

    pdfs = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    if not pdfs:
        print("⚠️ No hay PDFs en 2023")
        return

    for pdf in pdfs:
        ruta = os.path.join(PDF_DIR, pdf)
        nombre_base = f"2023_{os.path.splitext(pdf)[0]}"

        print(f"Procesando {pdf}...")

        resultados = procesar_pdf(ruta)
        guardar_resultados(resultados, nombre_base)

    print("✅ 2023 procesado")


if __name__ == "__main__":
    main()