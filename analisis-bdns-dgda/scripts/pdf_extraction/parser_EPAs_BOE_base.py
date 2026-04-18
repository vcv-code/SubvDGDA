from bs4 import BeautifulSoup
import requests


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


def parse_float(valor):
    if not valor:
        return None
    valor = valor.strip().replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return None


def detectar_estado_desde_caption(tabla):
    """
    BUG FIX 2021: en el BOE-A-2022-602 los títulos de sección están dentro
    de <caption><p>...</p></caption> de cada tabla, no en un <p> independiente
    previo. BeautifulSoup devuelve la tabla ANTES que su <p> de caption en el
    recorrido DFS, así que el estado del párrafo llega tarde. Esta función
    lee el caption de la tabla para saber su estado real antes de procesarla.
    """
    caption = tabla.find("caption")
    if not caption:
        return None
    return detectar_estado(caption.get_text(" ", strip=True))


def safe_get(celdas, idx):
    if idx is None or idx >= len(celdas):
        return None
    return celdas[idx].get_text(" ", strip=True)


def limpiar_header(th):
    return " ".join(th.stripped_strings).lower()


def mapear_indices(headers):
    """
    BUG FIX: se prioriza 'cuantía' / 'importe' ANTES de 'entidad' para evitar
    que cabeceras tipo 'Cuantía concedida a la entidad' se mapeen como entidad.
    """
    mapa = {}
    for i, h in enumerate(headers):
        if "expediente" in h:
            mapa["expediente"] = i
        elif "cuantía" in h or ("importe" in h and "entidad" not in h) or "concedido" in h:
            mapa["importe"] = i
        elif "entidad" in h:
            mapa["entidad"] = i
        elif "cif" in h or "nif" in h:
            mapa["cif"] = i
        elif "puntu" in h or "ptos" in h or "valoraci" in h:
            mapa["puntuacion"] = i
    return mapa


# =========================
# AÑO DESDE EXPEDIENTE
# BUG FIX: dos formatos distintos según año
#   2021: SUBVNNNYYYY  → últimos 4 dígitos son el año  (ej: SUBV2272021)
#   2022: SUBVYYYYNNN  → posiciones [4:8] son el año   (ej: SUBV2022094)
#   2023+: 2023B001    → primeros 4 dígitos            (ej: 2023B628)
# Se valida que el año esté en rango plausible (2018-2035).
# =========================

def extraer_anio_expediente(expediente):
    if not expediente:
        return None

    expediente = expediente.strip()

    # Formato 2023+: empieza por dígitos
    if expediente[:4].isdigit():
        anio = int(expediente[:4])
        if 2018 <= anio <= 2035:
            return anio

    if expediente.startswith("SUBV"):
        # Intento 1: posiciones [4:8] — formato SUBVYYYYNNN (2022)
        posible = expediente[4:8]
        if posible.isdigit() and 2018 <= int(posible) <= 2035:
            return int(posible)

        # Intento 2: últimas 4 posiciones — formato SUBVNNNYYYY (2021)
        posible = expediente[-4:]
        if posible.isdigit() and 2018 <= int(posible) <= 2035:
            return int(posible)

    return None


# =========================
# ESTADO
# BUG FIX: añadir "desestimad" como sinónimo de denegada.
# Los BOE de 2021-2023 usan "DESESTIMADAS" en lugar de "DENEGADAS".
# Sin este cambio, esos registros se quedaban pegados al estado anterior
# (desistida), contaminando el conteo.
# =========================

def detectar_estado(texto):
    texto = texto.lower()

    if "desistid" in texto or "renunci" in texto:
        return "desistida"

    elif "exclu" in texto:
        return "excluida"

    elif "no adquieren" in texto or "deneg" in texto or "desestimad" in texto:
        return "denegada"

    elif "beneficiari" in texto or "concedida" in texto:
        return "concedida"

    return None


# =========================
# PARSER BASE (2021–2024)
# =========================

def parsear_boe_epa_base(url, anio):

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "xml")

    resultados = []
    estado_actual = None

    for el in soup.find_all(["p", "table"]):

        # -------- ESTADO --------
        if el.name == "p":
            texto = el.get_text(" ", strip=True)
            nuevo_estado = detectar_estado(texto)
            if nuevo_estado:
                estado_actual = nuevo_estado

        # -------- TABLAS --------
        elif el.name == "table":

            if not estado_actual:
                continue

            # BUG FIX 2021: en BOE-A-2022-602 el título de sección está en
            # <caption> dentro de la tabla. El caption se lee ANTES de procesar
            # las filas para obtener el estado correcto de esta tabla.
            caption_estado = detectar_estado_desde_caption(el)
            estado_tabla = caption_estado if caption_estado else estado_actual

            headers = [limpiar_header(th) for th in el.find_all("th")]

            if not headers:
                continue

            mapa = mapear_indices(headers)

            if "expediente" not in mapa and "entidad" not in mapa:
                continue

            for fila in el.find_all("tr"):
                celdas = fila.find_all("td")

                if not celdas:
                    continue

                expediente = limpiar_texto(safe_get(celdas, mapa.get("expediente")))

                data = {
                    "anio": extraer_anio_expediente(expediente) or anio,
                    "num_expediente": expediente,
                    "entidad": limpiar_texto(safe_get(celdas, mapa.get("entidad"))),
                    "cif": limpiar_cif(safe_get(celdas, mapa.get("cif"))),
                    "puntuacion": None,
                    "importe": None,
                    "estado": estado_tabla
                }

                if "puntuacion" in mapa:
                    data["puntuacion"] = parse_float(safe_get(celdas, mapa["puntuacion"]))

                if "importe" in mapa:
                    data["importe"] = parse_float(safe_get(celdas, mapa["importe"]))

                # Regla clave: si hay importe → concedida (independientemente del estado del párrafo)
                if data["importe"] is not None:
                    data["estado"] = "concedida"

                resultados.append(data)

    return resultados
