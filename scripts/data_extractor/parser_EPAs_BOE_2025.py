from bs4 import BeautifulSoup
import requests
import re


# =========================
# UTILIDADES
# =========================

def limpiar_texto(texto):
    if not texto:
        return None
    return texto.strip()


def limpiar_cif(cif):
    cif = limpiar_texto(cif)
    if not cif or cif in ["–", "-", ""]:
        return None
    return cif


def safe_get(celdas, idx):
    if idx is None or idx >= len(celdas):
        return None
    return celdas[idx].get_text(" ", strip=True)


def limpiar_header(th):
    return " ".join(th.stripped_strings).lower()


def mapear_indices(headers):
    """
    BUG FIX: se prioriza 'cuantía' / 'importe' ANTES de 'entidad'.
    En el BOE 2025, la columna de importe puede tener cabecera
    'Cuantía concedida a la entidad', que contiene la palabra 'entidad'.
    Si no se prioriza, esa columna se mapea como entidad y el campo
    entidad recibe el valor numérico del importe en lugar del nombre.
    """
    mapa = {}
    for i, h in enumerate(headers):
        if "expediente" in h:
            mapa["expediente"] = i
        elif "cuantía" in h or ("importe" in h and "entidad" not in h):
            mapa["importe_idx"] = i
        elif "entidad" in h:
            mapa["entidad"] = i
        elif "cif" in h or "nif" in h:
            mapa["cif"] = i
    return mapa


# =========================
# EXTRACTORES HEURÍSTICOS
# Se usan para columnas de puntuación e importe cuyo header
# no está siempre presente o varía entre anexos.
# =========================

def _parece_numero_europeo(texto):
    """True si el texto es un número con formato europeo (coma decimal)."""
    if "," not in texto:
        return False
    try:
        float(texto.replace(".", "").replace(",", "."))
        return True
    except:
        return False


def _es_cif(texto):
    return bool(re.match(r'^[A-Za-z]\d{7}[A-Za-z0-9]$', texto.strip()))


def _es_expediente(texto):
    return bool(re.match(r'^\d{4}B\d+$', texto.strip()))


def extraer_puntos_2025(celdas):
    """Busca una celda con valor numérico entre 0 y 100 (puntuación)."""
    for celda in celdas:
        texto = celda.get_text(" ", strip=True)
        if "," in texto:
            try:
                num = float(texto.replace(".", "").replace(",", "."))
                if 0 <= num <= 100:
                    return num
            except:
                pass
    return None


def extraer_importe_2025(celdas):
    """Busca una celda con valor numérico mayor de 100 (importe en euros)."""
    for celda in celdas:
        texto = celda.get_text(" ", strip=True)
        if "," in texto:
            try:
                num = float(texto.replace(".", "").replace(",", "."))
                if num > 100:
                    return num
            except:
                pass
    return None


def extraer_entidad_2025(celdas, idx_entidad_mapeado):
    """
    BUG FIX: extrae el nombre de entidad de forma robusta.

    Primero intenta el índice mapeado por cabecera. Si ese valor
    parece un número (importe) o un CIF, busca en todas las celdas
    la primera que sea texto largo no numérico → nombre de entidad.
    """
    # Intento 1: índice mapeado
    if idx_entidad_mapeado is not None:
        texto = safe_get(celdas, idx_entidad_mapeado) or ""
        if texto and not _parece_numero_europeo(texto) and not _es_cif(texto) and not _es_expediente(texto):
            return texto.strip()

    # Intento 2: heurística — primera celda con texto largo y no numérico
    for celda in celdas:
        texto = celda.get_text(" ", strip=True)
        if (len(texto) > 8
                and not _parece_numero_europeo(texto)
                and not _es_cif(texto)
                and not _es_expediente(texto)):
            return texto
    return None


# =========================
# PARSER 2025
# =========================

def parsear_boe_epa_2025(url):

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "xml")

    resultados = []
    estado_actual = None

    for el in soup.find_all(["p", "table"]):

        # -------- ESTADO --------
        if el.name == "p":
            texto = el.get_text(" ", strip=True).lower()

            if "beneficiarias" in texto:
                estado_actual = "concedida"
            elif "exclu" in texto:
                estado_actual = "excluida"
            elif "no adquieren" in texto or "desestimad" in texto or "deneg" in texto:
                estado_actual = "denegada"
            elif "desistidas" in texto or "renunci" in texto:
                estado_actual = "desistida"

        # -------- TABLAS --------
        elif el.name == "table":

            if not estado_actual:
                continue

            headers = [limpiar_header(th) for th in el.find_all("th")]

            if not headers:
                continue

            mapa = mapear_indices(headers)

            for fila in el.find_all("tr"):
                celdas = fila.find_all("td")

                if not celdas:
                    continue

                expediente = limpiar_texto(safe_get(celdas, mapa.get("expediente")))

                data = {
                    "anio": 2025,
                    "num_expediente": expediente,
                    "entidad": extraer_entidad_2025(celdas, mapa.get("entidad")),
                    "cif": limpiar_cif(safe_get(celdas, mapa.get("cif"))),
                    "puntuacion": extraer_puntos_2025(celdas),
                    "importe": extraer_importe_2025(celdas),
                    "estado": estado_actual
                }

                # Regla clave: si hay importe → concedida
                if data["importe"] is not None:
                    data["estado"] = "concedida"

                resultados.append(data)

    return resultados
