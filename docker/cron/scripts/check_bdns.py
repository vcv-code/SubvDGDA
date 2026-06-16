#!/usr/bin/env python3
"""
check_bdns.py — Comprueba nuevas convocatorias DGDA en la API BDNS y detecta resoluciones.

Lógica (orden de ejecución):
  1. Comprueba si las convocatorias del año actual con fecha_resolucion=NULL
     ya tienen resolución publicada en la API BDNS. Si la tienen, actualiza
     la BD → el banner de la home desaparece automáticamente.
  2. Si aún faltan convocatorias por registrar, consulta la API BDNS para
     detectar nuevas convocatorias DGDA del año actual.
  3. Para cada convocatoria nueva:
     · Detecta el tipo (eell / epa) por palabras clave del título.
     · Inserta en convocatorias con fecha_resolucion = NULL.
     · Actualiza el fichero de estado del año.
  4. Guarda el estado actualizado.

El paso 1 corre siempre (aunque EELL y EPA ya estén registradas) para que
las resoluciones se detecten automáticamente sin intervención manual.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

import pymysql
import requests

BDNS_API  = "https://www.infosubvenciones.es/bdnstrans/api"
YEAR      = datetime.now().year
LOG_DIR   = "/app/logs/cron"
STATE_FILE = f"{LOG_DIR}/estado_{YEAR}.json"
LOG_FILE  = f"{LOG_DIR}/bdns_check.log"

DB_HOST     = os.environ.get("DB_HOST", "db")
DB_PORT     = int(os.environ.get("DB_PORT", 3306))
DB_NAME     = os.environ.get("DB_NAME", "bdns_dgda")
DB_USER     = os.environ.get("DB_USER", "bdns_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "bdns_pass")

# Reintentos para llamadas a la API BDNS — backoff exponencial 2s, 4s, 8s
MAX_INTENTOS_BDNS = 3
BACKOFF_INICIAL   = 2

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()
log.addHandler(logging.StreamHandler(sys.stdout))


# ──────────────────────────────────────────────
# Estado
# ──────────────────────────────────────────────

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"eell": False, "epa": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ──────────────────────────────────────────────
# Base de datos
# ──────────────────────────────────────────────

def get_db():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, db=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, charset="utf8mb4",
    )


def convocatoria_existe(conn, num_convoc):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_convoc FROM convocatorias WHERE num_convoc = %s",
            (str(num_convoc),),
        )
        return cur.fetchone() is not None


_TITULO_NORMALIZADO = {
    "epa":  "Subvenciones a entidades de protección animal {year}",
    "eell": "Subvenciones a entidades locales para protección animal {year}",
}


def insertar_convocatoria(conn, tipo, num_convoc, titulo, fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None
    except (ValueError, TypeError):
        fecha = None
    titulo_final = _TITULO_NORMALIZADO.get(tipo, titulo).format(year=YEAR)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO convocatorias
                (num_convoc, titulo_convoc, tipo_convoc, anio_convocatoria,
                 fecha_convocatoria, fecha_resolucion, periodo_meses)
            VALUES (%s, %s, %s, %s, %s, NULL, 12)
            """,
            (str(num_convoc), titulo_final, tipo, YEAR, fecha),
        )
    conn.commit()


def actualizar_fecha_resolucion(conn, id_convoc, fecha):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE convocatorias SET fecha_resolucion = %s WHERE id_convoc = %s",
            (fecha, id_convoc),
        )
    conn.commit()


# ──────────────────────────────────────────────
# API BDNS
# ──────────────────────────────────────────────

def detectar_tipo(descripcion):
    desc = descripcion.upper()
    if "ENTIDADES LOCALES" in desc or "EELL" in desc:
        return "eell"
    if "ENTIDADES PRIVADAS" in desc or "ASOCIACIONES" in desc or "PROTECCI" in desc:
        return "epa"
    return None


def parsear_fecha(fecha_str):
    """Acepta DD/MM/YYYY o YYYY-MM-DD. Devuelve date o None."""
    if not fecha_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None


def _get_bdns_con_retry(url, params=None):
    """
    Hace GET a la API BDNS con reintentos y backoff exponencial.

    BDNS puede tener fallos transitorios (502 momentáneo, timeout puntual).
    Sin retry, una sola incidencia hace perder hasta 4 días hasta el
    siguiente ciclo del cron. Con 3 intentos y backoff (2s, 4s, 8s) la
    función absorbe blips de hasta ~15 segundos.

    Devuelve la response si tuvo éxito (HTTP 200), None si todos los
    intentos fallaron (errores de red o status != 200).
    """
    for intento in range(1, MAX_INTENTOS_BDNS + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp
            log.warning(
                "BDNS devolvió %d en intento %d/%d para %s",
                resp.status_code, intento, MAX_INTENTOS_BDNS, url,
            )
        except requests.RequestException as e:
            log.warning(
                "Intento %d/%d fallido para %s: %s",
                intento, MAX_INTENTOS_BDNS, url, e,
            )

        if intento < MAX_INTENTOS_BDNS:
            espera = BACKOFF_INICIAL * (2 ** (intento - 1))  # 2, 4, 8
            log.info("Esperando %ds antes de reintentar...", espera)
            time.sleep(espera)

    log.error("BDNS no respondió tras %d intentos: %s", MAX_INTENTOS_BDNS, url)
    return None


def consultar_resolucion_bdns(num_convoc):
    """
    Consulta el detalle de una convocatoria en la API BDNS y devuelve
    la fecha de resolución si ya está publicada, o None si no.

    La API devuelve el campo fechaResolucion cuando la convocatoria
    ya tiene resolución registrada en BDNS (habitualmente 1-2 días
    después de la publicación en el BOE).
    """
    resp = _get_bdns_con_retry(f"{BDNS_API}/convocatorias/{num_convoc}")
    if resp is None:
        return None
    data = resp.json()
    # Intentar los dos nombres de campo que usa la API BDNS
    fecha_str = data.get("fechaResolucion") or data.get("fechaPublicacionResolucion")
    return parsear_fecha(fecha_str)


def comprobar_resoluciones(conn):
    """
    Para cada convocatoria del año actual sin fecha_resolucion en la BD,
    consulta la API BDNS. Si ya tiene resolución publicada la registra
    en la BD → el banner de avisos desaparece automáticamente.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id_convoc, num_convoc, tipo_convoc
            FROM convocatorias
            WHERE fecha_resolucion IS NULL
              AND num_convoc IS NOT NULL
              AND anio_convocatoria = %s
            """,
            (YEAR,),
        )
        pendientes = cur.fetchall()

    if not pendientes:
        return

    log.info(
        "Comprobando resolución en BDNS para %d convocatoria(s) pendiente(s)...",
        len(pendientes),
    )
    for id_convoc, num_convoc, tipo in pendientes:
        fecha_res = consultar_resolucion_bdns(num_convoc)
        if fecha_res:
            actualizar_fecha_resolucion(conn, id_convoc, fecha_res)
            log.info(
                "Resolución detectada y registrada: %s (convoc. %s) — %s",
                tipo.upper(), num_convoc, fecha_res,
            )
        else:
            log.info(
                "Convocatoria %s (%s) aún sin resolución en BDNS.",
                tipo.upper(), num_convoc,
            )


def buscar_en_bdns(termino_busqueda):
    """Devuelve convocatorias DGDA del año actual encontradas en la API BDNS."""
    resultados = []
    page = 0
    while True:
        params = {
            "page": page, "pageSize": 50,
            "order": "numeroConvocatoria", "direccion": "desc",
            "vpd": "GE",
            "descripcion": termino_busqueda,
            "descripcionTipoBusqueda": 0,
            "mrr": "false", "contribucion": "false",
            "fechaDesde": f"01/01/{YEAR}",
            "fechaHasta": datetime.now().strftime("%d/%m/%Y"),
            "tipoAdministracion": "C",
        }
        resp = _get_bdns_con_retry(
            f"{BDNS_API}/convocatorias/busqueda", params=params
        )
        if resp is None:
            log.error("Búsqueda BDNS abandonada para %s tras reintentos", termino_busqueda)
            break
        data = resp.json()

        for c in data.get("content", []):
            nivel3 = (c.get("nivel3") or "").upper()
            desc   = (c.get("descripcion") or "").upper()
            if "DERECHOS DE LOS ANIMALES" in nivel3 and "SUBVENCIONES" in desc:
                resultados.append(c)

        if page >= data.get("totalPages", 1) - 1:
            break
        page += 1

    return resultados


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    log.info("=== Inicio check_bdns — %s ===", datetime.now().strftime("%Y-%m-%d"))
    state = load_state()

    try:
        conn = get_db()
    except Exception as e:
        log.error("No se pudo conectar a la BD: %s", e)
        sys.exit(1)

    try:
        # Paso 1: detectar resoluciones publicadas en BDNS (corre siempre)
        comprobar_resoluciones(conn)

        # Paso 2: buscar nuevas convocatorias solo si aún faltan
        if state["eell"] and state["epa"]:
            log.info(
                "Temporada %s completada (EELL y EPA registradas). Solo se comprobaron resoluciones.",
                YEAR,
            )
            return

        convocatorias  = buscar_en_bdns("protección animal")
        convocatorias += buscar_en_bdns("colonias felinas")

        if not convocatorias:
            log.info("API BDNS: sin resultados para %s.", YEAR)
        else:
            log.info(
                "API BDNS: %d convocatoria(s) encontrada(s) para %s.",
                len(convocatorias), YEAR,
            )

        for c in convocatorias:
            num   = c.get("numeroConvocatoria")
            titulo = c.get("descripcion", "Sin título")
            fecha  = c.get("fechaRecepcion")
            tipo   = detectar_tipo(titulo)

            if tipo is None:
                log.warning(
                    "Tipo no detectado para convocatoria %s — '%s'. Omitida.", num, titulo
                )
                continue

            if state[tipo]:
                log.info("Convocatoria %s (%s) ya procesada este año.", tipo.upper(), num)
                continue

            if convocatoria_existe(conn, num):
                log.info(
                    "Convocatoria %s ya existe en BD. Marcando %s como encontrada.",
                    num, tipo.upper(),
                )
                state[tipo] = True
            else:
                insertar_convocatoria(conn, tipo, num, titulo, fecha)
                log.info(
                    "NUEVA convocatoria %s insertada: %s — '%s' (%s)",
                    tipo.upper(), num, titulo, fecha or "sin fecha",
                )
                # La convocatoria se inserta sin fecha de fin de plazo (BDNS no la da
                # de forma fiable). Aviso para que se rellene desde el panel admin.
                log.warning(
                    "ACCIÓN REQUERIDA: la convocatoria %s (%s) se ha insertado SIN fecha de fin de plazo. "
                    "Rellénala en el panel admin (Avisos / Banners) para que el banner muestre 'plazo abierto/cerrado'.",
                    tipo.upper(), num,
                )
                state[tipo] = True

    finally:
        conn.close()
        save_state(state)
        log.info("Estado guardado: %s", state)
        log.info("=== Fin check_bdns ===\n")


if __name__ == "__main__":
    main()
