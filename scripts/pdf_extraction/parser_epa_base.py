import pdfplumber
import json
import os
import logging
import re
import unicodedata
from datetime import datetime

# --- CONFIGURACIÓN ---

BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, "../../data/raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "../../data/processed")

# Tipos de anexos que aparecen en los PDFs
ANEXOS = {
    "admitidas_no_beneficiarias": "NO ADQUIEREN LA CONDICI",
    "beneficiarias": "ADQUIEREN LA CONDI",
    "excluidas": "SOLICITUDES EXCLUIDAS",
    "desistidas": "SOLICITUDES DESISTIDAS"
}

# Columnas esperadas por tipo de anexo
CABECERAS = {
    "beneficiarias": ["num_expediente", "cif", "entidad", "puntos", "importe"],
    "admitidas_no_beneficiarias": ["num_expediente", "cif", "entidad", "puntos"],
    "excluidas": ["num_expediente", "cif", "entidad", "causas_exclusion"],
    "desistidas": ["num_expediente", "cif", "entidad"]
}

# Para detectar filas de cabecera dentro de las tablas
TEXTOS_CABECERA = {
    "num_expediente": ["nº", "expediente"],
    "cif": ["cif"],
    "entidad": ["entidad"],
    "puntos": ["puntos", "total"],
    "importe": ["importe", "asignacion"]
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# --- FUNCIONES DE LIMPIEZA ---

def limpiar_texto(texto):
    """Elimina saltos de línea y espacios duplicados"""
    if not texto:
        return ""
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpiar_cif(cif):
    """Si hay varios CIF, se queda con el primero"""
    if not cif:
        return None
    return cif.split()[0]


def limpiar_puntos(valor):
    """Extrae número válido de puntuación"""
    if not valor:
        return None

    valor = str(valor).lower()

    if "no aplica" in valor or "recurso" in valor:
        return None

    match = re.search(r"\d+([.,]\d+)?", valor)

    if match:
        return float(match.group(0).replace(",", "."))

    return None


# --- UTILIDADES BASE ---

def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return texto.upper()


def detectar_anexo(texto_pagina):
    texto = normalizar_texto(texto_pagina)

    for clave, fragmento in ANEXOS.items():
        if re.search(fragmento, texto):
            return clave

    return None


def limpiar_fila(fila):
    return [str(celda).strip() if celda is not None else "" for celda in fila]


def es_fila_cabecera(fila_dict):
    for campo, textos in TEXTOS_CABECERA.items():
        valor = fila_dict.get(campo, "").lower().strip()
        if any(texto in valor for texto in textos):
            return True
    return False


def es_texto_basura(fila_limpia):
    texto = " ".join(fila_limpia).lower()

    patrones = [
        "codigo seguro",
        "csv",
        "direccion de validacion",
        "firmante",
        "sede.administracion",
        "fecha :"
    ]

    return any(p in texto for p in patrones)


def es_expediente_valido(valor):
    if not valor:
        return False

    valor = valor.strip()
    return bool(re.match(r"\d{4}[A-Z]\d+", valor))


def parsear_importe(valor):
    if not valor:
        return None

    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return None


def reconstruir_filas(tabla, num_cols):
    """
    Une filas partidas en múltiples líneas
    """
    filas_reconstruidas = []
    fila_actual = None

    for fila in tabla:
        fila_limpia = limpiar_fila(fila)

        if len(fila_limpia) < num_cols:
            fila_limpia += [""] * (num_cols - len(fila_limpia))

        if fila_limpia[0].strip():
            if fila_actual:
                filas_reconstruidas.append(fila_actual)
            fila_actual = fila_limpia
        else:
            if fila_actual:
                fila_actual = [
                    (a + " " + b).strip() if b else a
                    for a, b in zip(fila_actual, fila_limpia)
                ]

    if fila_actual:
        filas_reconstruidas.append(fila_actual)

    return filas_reconstruidas


# --- CORE PRINCIPAL ---

def extraer_tablas_pdf(ruta_pdf):
    resultados = {clave: [] for clave in ANEXOS}
    anexo_actual = None

    logging.info(f"Procesando: {os.path.basename(ruta_pdf)}")

    with pdfplumber.open(ruta_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages, start=1):

            texto = pagina.extract_text() or ""
            anexo_detectado = detectar_anexo(texto)

            if anexo_detectado:
                anexo_actual = anexo_detectado
                logging.info(f"  Página {num_pagina}: anexo '{anexo_actual}'")

            elif "ANEXO" in texto.upper():
                anexo_actual = None

            if anexo_actual is None:
                continue

            tablas = pagina.extract_tables()

            for tabla in tablas:
                if not tabla or len(tabla) < 2:
                    continue

                cabecera = CABECERAS.get(anexo_actual)
                if not cabecera:
                    continue

                num_cols = len(cabecera)
                filas = reconstruir_filas(tabla, num_cols)

                for fila_limpia in filas:

                    if all(c == "" for c in fila_limpia):
                        continue

                    if es_texto_basura(fila_limpia):
                        continue

                    if len(fila_limpia) != num_cols:
                        continue

                    fila_dict = dict(zip(cabecera, fila_limpia))

                    # --- LIMPIEZA ---
                    fila_dict["entidad"] = limpiar_texto(fila_dict.get("entidad"))
                    fila_dict["cif"] = limpiar_cif(fila_dict.get("cif"))

                    if "puntos" in fila_dict:
                        fila_dict["puntos"] = limpiar_puntos(fila_dict.get("puntos"))

                    if es_fila_cabecera(fila_dict):
                        continue

                    if not es_expediente_valido(fila_dict.get("num_expediente")):
                        continue

                    if "importe" in fila_dict:
                        fila_dict["importe"] = parsear_importe(fila_dict["importe"])

                    fila_dict["_meta"] = {
                        "pdf": os.path.basename(ruta_pdf),
                        "pagina": num_pagina,
                        "anexo": anexo_actual
                    }

                    resultados[anexo_actual].append(fila_dict)

    return resultados


# --- GUARDADO CONTROLADO ---

def guardar_resultados(resultados, nombre_base):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for anexo, datos in resultados.items():
        if not datos:
            logging.info(f"  Anexo '{anexo}': sin datos")
            continue

        # 🔹 ordenar resultados
        datos = sorted(datos, key=lambda x: (x.get("num_expediente") or ""))

        nombre_archivo = f"{nombre_base}_{anexo}.json"
        ruta = os.path.join(OUTPUT_DIR, nombre_archivo)

        # 🔹 sobrescribir limpio
        if os.path.exists(ruta):
            os.remove(ruta)

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        logging.info(f"  Guardado: {nombre_archivo} ({len(datos)} filas)")


# --- MAIN (NO USAR PARA EPA YA, PERO LO DEJO) ---

def main():
    if not os.path.exists(PDF_DIR):
        logging.error("No existe el directorio data/raw/")
        return

    pdfs = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdfs:
        logging.warning("No se encontraron PDFs")
        return

    for nombre_pdf in pdfs:
        ruta_pdf = os.path.join(PDF_DIR, nombre_pdf)
        nombre_base = os.path.splitext(nombre_pdf)[0]

        resultados = extraer_tablas_pdf(ruta_pdf)
        guardar_resultados(resultados, nombre_base)

    logging.info("Extracción completada.")


if __name__ == "__main__":
    main()