"""
cargar_dataset.py
Carga data/final/dataset_unificado.json en la base de datos bdns_dgda.

Orden de inserción (respeta FKs):
  1. convocatorias  → una fila por (anio, tipo)
  2. beneficiarios  → una fila por CIF único
  3. solicitudes    → una fila por registro
  4. concesiones    → solo registros con estado='concedida'

Uso:
  Desde la raíz del proyecto:
    python -m scripts.data_processing.cargar_dataset

  Variables de entorno opcionales (si la BD no está en Docker local):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import json
import os
import sys

import pymysql
import pymysql.cursors


# ──────────────────────────────────────────────
# Conexión
# ──────────────────────────────────────────────

DB_HOST     = os.environ.get("DB_HOST",     "127.0.0.1")
DB_PORT     = int(os.environ.get("DB_PORT", "3307"))   # puerto mapeado en docker-compose
DB_NAME     = os.environ.get("DB_NAME",     "bdns_dgda")
DB_USER     = os.environ.get("DB_USER",     "bdns_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "bdns_pass")


def conectar():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


# ──────────────────────────────────────────────
# Títulos de convocatoria (para la columna titulo_convoc)
# ──────────────────────────────────────────────

_TITULO = {
    (2021, "epa"):  "Subvenciones a entidades protectoras de animales 2021",
    (2022, "epa"):  "Subvenciones a entidades protectoras de animales 2022",
    (2023, "epa"):  "Subvenciones a entidades protectoras de animales 2023 (semestral)",
    (2024, "epa"):  "Subvenciones a entidades protectoras de animales 2024 (semestral)",
    (2025, "epa"):  "Subvenciones a entidades protectoras de animales 2025",
    (2023, "eell"): "Subvenciones a entidades locales para protección animal 2023",
    (2024, "eell"): "Subvenciones a entidades locales para protección animal 2024",
    (2025, "eell"): "Subvenciones a entidades locales para protección animal 2025",
}

_PERIODO = {
    (2023, "epa"): 6,
    (2024, "epa"): 6,
}


# ──────────────────────────────────────────────
# Paso 1: Convocatorias
# ──────────────────────────────────────────────

def cargar_convocatorias(cursor, registros):
    """Inserta una convocatoria por (anio, tipo). Devuelve dict {(anio,tipo): id_convoc}."""
    convocs = sorted(set((r["anio"], r["tipo"]) for r in registros))

    sql = """
        INSERT INTO convocatorias (titulo_convoc, tipo_convoc, anio_convocatoria, periodo_meses)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE id_convoc = LAST_INSERT_ID(id_convoc)
    """
    # No hay UNIQUE KEY natural en convocatorias; usamos SELECT para evitar duplicados
    mapa = {}
    for anio, tipo in convocs:
        cursor.execute(
            "SELECT id_convoc FROM convocatorias WHERE anio_convocatoria = %s AND tipo_convoc = %s",
            (anio, tipo),
        )
        fila = cursor.fetchone()
        if fila:
            mapa[(anio, tipo)] = fila["id_convoc"]
        else:
            periodo = _PERIODO.get((anio, tipo), 12)
            titulo  = _TITULO.get((anio, tipo), f"Convocatoria {tipo.upper()} {anio}")
            cursor.execute(
                "INSERT INTO convocatorias (titulo_convoc, tipo_convoc, anio_convocatoria, periodo_meses) "
                "VALUES (%s, %s, %s, %s)",
                (titulo, tipo, anio, periodo),
            )
            mapa[(anio, tipo)] = cursor.lastrowid

    print(f"  Convocatorias: {len(mapa)} filas")
    return mapa


# ──────────────────────────────────────────────
# Paso 2: Beneficiarios
# ──────────────────────────────────────────────

def cargar_beneficiarios(cursor, registros):
    """Inserta una fila por CIF único. Devuelve dict {cif: id_benef}."""
    # Agrupa por CIF; si CIF es None, usa nombre como clave fallback
    vistos = {}  # cif_o_nombre → (cif, nombre, tipo_benef)
    for r in registros:
        cif   = r.get("cif") or None
        nombre = r["entidad"]
        tipo   = "asociacion" if r["tipo"] == "epa" else "entidad_local"
        clave  = cif if cif else f"__nombre__{nombre}"
        if clave not in vistos:
            vistos[clave] = (cif, nombre, tipo)

    mapa = {}  # cif_o_nombre → id_benef
    for clave, (cif, nombre, tipo) in vistos.items():
        if cif:
            cursor.execute("SELECT id_benef FROM beneficiarios WHERE cif = %s", (cif,))
            fila = cursor.fetchone()
            if fila:
                mapa[clave] = fila["id_benef"]
            else:
                cursor.execute(
                    "INSERT INTO beneficiarios (cif, nombre, tipo_benef) VALUES (%s, %s, %s)",
                    (cif, nombre, tipo),
                )
                mapa[clave] = cursor.lastrowid
        else:
            # Sin CIF: busca por nombre exacto
            cursor.execute("SELECT id_benef FROM beneficiarios WHERE nombre = %s AND cif IS NULL", (nombre,))
            fila = cursor.fetchone()
            if fila:
                mapa[clave] = fila["id_benef"]
            else:
                cursor.execute(
                    "INSERT INTO beneficiarios (cif, nombre, tipo_benef) VALUES (%s, %s, %s)",
                    (None, nombre, tipo),
                )
                mapa[clave] = cursor.lastrowid

    print(f"  Beneficiarios: {len(mapa)} filas")
    return mapa


# ──────────────────────────────────────────────
# Paso 3: Solicitudes
# ──────────────────────────────────────────────

def cargar_solicitudes(cursor, registros, mapa_convoc, mapa_benef):
    """Inserta solicitudes. Devuelve dict {indice_registro: id_solic}."""
    mapa_solic = {}
    insertadas = 0
    omitidas   = 0

    for i, r in enumerate(registros):
        id_convoc = mapa_convoc[(r["anio"], r["tipo"])]

        cif   = r.get("cif") or None
        clave = cif if cif else f"__nombre__{r['entidad']}"
        id_benef = mapa_benef[clave]

        num_exp    = r.get("num_expediente") or None
        puntuacion = r.get("puntuacion")
        estado     = r["estado"]

        # Comprueba si ya existe (num_expediente + id_convoc)
        if num_exp:
            cursor.execute(
                "SELECT id_solic FROM solicitudes WHERE num_expediente = %s AND id_convoc = %s",
                (num_exp, id_convoc),
            )
            fila = cursor.fetchone()
            if fila:
                mapa_solic[i] = fila["id_solic"]
                omitidas += 1
                continue

        cursor.execute(
            "INSERT INTO solicitudes (id_convoc, id_benef, num_expediente, puntuacion, estado) "
            "VALUES (%s, %s, %s, %s, %s)",
            (id_convoc, id_benef, num_exp, puntuacion, estado),
        )
        mapa_solic[i] = cursor.lastrowid
        insertadas += 1

    print(f"  Solicitudes: {insertadas} insertadas, {omitidas} ya existían")
    return mapa_solic


# ──────────────────────────────────────────────
# Paso 4: Concesiones
# ──────────────────────────────────────────────

def cargar_concesiones(cursor, registros, mapa_solic):
    """Inserta concesiones solo para registros con estado='concedida'."""
    insertadas = 0
    omitidas   = 0

    for i, r in enumerate(registros):
        if r["estado"] != "concedida":
            continue

        id_solic = mapa_solic.get(i)
        if id_solic is None:
            continue

        importe = r.get("importe") or 0.00
        linea   = r.get("linea")   or None
        tramo   = r.get("tramo")   or None

        cursor.execute(
            "SELECT id_conces FROM concesiones WHERE id_solic = %s", (id_solic,)
        )
        if cursor.fetchone():
            omitidas += 1
            continue

        cursor.execute(
            "INSERT INTO concesiones (id_solic, importe, linea, tramo) VALUES (%s, %s, %s, %s)",
            (id_solic, importe, linea, tramo),
        )
        insertadas += 1

    print(f"  Concesiones: {insertadas} insertadas, {omitidas} ya existían")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    ruta = os.path.join(os.path.dirname(__file__), "../../data/final/dataset_unificado.json")
    ruta = os.path.normpath(ruta)

    print(f"Cargando dataset: {ruta}")
    with open(ruta, encoding="utf-8") as f:
        registros = json.load(f)
    print(f"  {len(registros)} registros leídos")

    try:
        conn = conectar()
    except Exception as e:
        print(f"\nERROR al conectar con la base de datos: {e}")
        print("Comprueba que el contenedor Docker está activo y las credenciales son correctas.")
        sys.exit(1)

    try:
        with conn.cursor() as cursor:
            print("\n[1/4] Convocatorias...")
            mapa_convoc = cargar_convocatorias(cursor, registros)

            print("[2/4] Beneficiarios...")
            mapa_benef = cargar_beneficiarios(cursor, registros)

            print("[3/4] Solicitudes...")
            mapa_solic = cargar_solicitudes(cursor, registros, mapa_convoc, mapa_benef)

            print("[4/4] Concesiones...")
            cargar_concesiones(cursor, registros, mapa_solic)

        conn.commit()
        print("\nCarga completada correctamente.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR durante la carga: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
