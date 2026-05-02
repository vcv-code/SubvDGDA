#!/usr/bin/env python3
"""
check_bdns.py — Comprueba nuevas convocatorias DGDA en la API BDNS.

Lógica:
  1. Lee el fichero de estado del año actual (logs/cron/estado_YYYY.json).
     Si ya constan EELL y EPA como encontradas → sale sin consultar la API.
  2. Consulta la API BDNS filtrando por año actual y organismo DGDA.
  3. Para cada convocatoria nueva (no existe en BD por num_convoc):
     - Detecta el tipo (eell / epa) por palabras clave del título.
     - Inserta en la tabla convocatorias con fecha_resolucion = NULL.
     - Actualiza el estado del año.
  4. Guarda el estado actualizado.

El campo fecha_resolucion = NULL es la señal que usa el backend (/avisos/)
para mostrar el banner "convocatoria en tramitación" en el frontend.
Cuando a fin de año se carguen los datos del BOE se actualizará ese campo
y el banner desaparecerá automáticamente.
"""

import json
import logging
import os
import sys
from datetime import datetime

import pymysql
import requests

BDNS_API = "https://www.infosubvenciones.es/bdnstrans/api"
YEAR = datetime.now().year
LOG_DIR = "/app/logs/cron"
STATE_FILE = f"{LOG_DIR}/estado_{YEAR}.json"
LOG_FILE = f"{LOG_DIR}/bdns_check.log"

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = os.environ.get("DB_NAME", "bdns_dgda")
DB_USER = os.environ.get("DB_USER", "bdns_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "bdns_pass")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()
log.addHandler(logging.StreamHandler(sys.stdout))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"eell": False, "epa": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        db=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
    )


def convocatoria_existe(conn, num_convoc):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id_convoc FROM convocatorias WHERE num_convoc = %s",
            (str(num_convoc),),
        )
        return cur.fetchone() is not None


def insertar_convocatoria(conn, tipo, num_convoc, titulo, fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None
    except (ValueError, TypeError):
        fecha = None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO convocatorias
                (num_convoc, titulo_convoc, tipo_convoc, anio_convocatoria,
                 fecha_convocatoria, fecha_resolucion, periodo_meses)
            VALUES (%s, %s, %s, %s, %s, NULL, 12)
            """,
            (str(num_convoc), titulo[:255], tipo, YEAR, fecha),
        )
    conn.commit()


def detectar_tipo(descripcion):
    """Determina si la convocatoria es EELL o EPA por palabras clave del título."""
    desc = descripcion.upper()
    if "ENTIDADES LOCALES" in desc or "EELL" in desc:
        return "eell"
    if "ENTIDADES PRIVADAS" in desc or "ASOCIACIONES" in desc:
        return "epa"
    return None


def buscar_en_bdns(termino_busqueda):
    """Devuelve convocatorias DGDA del año actual encontradas en la API BDNS."""
    resultados = []
    page = 0

    while True:
        params = {
            "page": page,
            "pageSize": 50,
            "order": "numeroConvocatoria",
            "direccion": "desc",
            "vpd": "GE",
            "descripcion": termino_busqueda,
            "descripcionTipoBusqueda": 0,
            "mrr": "false",
            "contribucion": "false",
            "fechaDesde": f"01/01/{YEAR}",
            "fechaHasta": datetime.now().strftime("%d/%m/%Y"),
            "tipoAdministracion": "C",
        }
        try:
            resp = requests.get(
                f"{BDNS_API}/convocatorias/busqueda", params=params, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            log.error("Error al consultar BDNS (%s): %s", termino_busqueda, e)
            break

        for c in data.get("content", []):
            nivel3 = (c.get("nivel3") or "").upper()
            desc = (c.get("descripcion") or "").upper()
            if "DERECHOS DE LOS ANIMALES" in nivel3 and "SUBVENCIONES" in desc:
                resultados.append(c)

        if page >= data.get("totalPages", 1) - 1:
            break
        page += 1

    return resultados


def main():
    log.info("=== Inicio check_bdns — %s ===", datetime.now().strftime("%Y-%m-%d"))
    state = load_state()

    if state["eell"] and state["epa"]:
        log.info("Temporada %s completada (EELL y EPA registradas). Sin acción.", YEAR)
        return

    try:
        conn = get_db()
    except Exception as e:
        log.error("No se pudo conectar a la BD: %s", e)
        sys.exit(1)

    try:
        convocatorias = buscar_en_bdns("protección animal")
        convocatorias += buscar_en_bdns("colonias felinas")

        if not convocatorias:
            log.info("API BDNS: sin resultados para %s.", YEAR)
        else:
            log.info("API BDNS: %d convocatoria(s) encontrada(s) para %s.", len(convocatorias), YEAR)

        for c in convocatorias:
            num = c.get("numeroConvocatoria")
            titulo = c.get("descripcion", "Sin título")
            fecha = c.get("fechaRecepcion")
            tipo = detectar_tipo(titulo)

            if tipo is None:
                log.warning("Tipo no detectado para convocatoria %s — '%s'. Omitida.", num, titulo)
                continue

            if state[tipo]:
                log.info("Convocatoria %s (%s) ya procesada este año.", tipo.upper(), num)
                continue

            if convocatoria_existe(conn, num):
                log.info("Convocatoria %s ya existe en BD. Marcando %s como encontrada.", num, tipo.upper())
                state[tipo] = True
            else:
                insertar_convocatoria(conn, tipo, num, titulo, fecha)
                log.info(
                    "NUEVA convocatoria %s insertada: %s — '%s' (%s)",
                    tipo.upper(), num, titulo, fecha or "sin fecha",
                )
                state[tipo] = True

    finally:
        conn.close()
        save_state(state)
        log.info("Estado guardado: %s", state)
        log.info("=== Fin check_bdns ===\n")


if __name__ == "__main__":
    main()
