"""
cargar_dataset.py
Carga data/final/dataset_unificado.json en la base de datos bdns_dgda.

Orden de inserción (respeta FKs):
  1. convocatorias       → una fila por (anio, tipo)
  2. beneficiarios       → una fila por CIF único (registros principales +
                           municipios miembro de agrupaciones EELL 2025)
  3. solicitudes         → una fila por registro
  4. concesiones         → solo registros con estado='concedida'
  5. agrupaciones        → una fila por concesión que sea agrupación EELL
  6. agrupacion_miembros → una fila por municipio miembro de cada agrupación

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

# Fechas oficiales obtenidas de la API BDNS (fecha_convocatoria)
# y de la API del BOE (fecha_resolucion = fecha de publicación en BOE).
_FECHAS = {
    (2021, "epa"):  ("2021-10-26", "2022-01-14"),
    (2022, "epa"):  ("2022-08-24", "2022-12-23"),
    (2023, "epa"):  ("2023-05-19", "2023-11-20"),
    (2024, "epa"):  ("2024-06-17", "2024-11-14"),
    (2025, "epa"):  ("2025-05-05", "2025-12-30"),
    (2023, "eell"): ("2023-05-19", "2024-01-11"),
    (2024, "eell"): ("2024-05-31", "2024-11-20"),
    (2025, "eell"): ("2025-03-27", "2025-12-31"),
}


# ──────────────────────────────────────────────
# Paso 1: Convocatorias
# ──────────────────────────────────────────────

def cargar_convocatorias(cursor, registros):
    """Inserta una convocatoria por (anio, tipo). Devuelve dict {(anio,tipo): id_convoc}."""
    convocs = sorted(set((r["anio"], r["tipo"]) for r in registros))

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
            fecha_conv, fecha_resol = _FECHAS.get((anio, tipo), (None, None))
            cursor.execute(
                "INSERT INTO convocatorias "
                "(titulo_convoc, tipo_convoc, anio_convocatoria, periodo_meses, "
                " fecha_convocatoria, fecha_resolucion) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (titulo, tipo, anio, periodo, fecha_conv, fecha_resol),
            )
            mapa[(anio, tipo)] = cursor.lastrowid

    print(f"  Convocatorias: {len(mapa)} filas")
    return mapa


# ──────────────────────────────────────────────
# Paso 2: Beneficiarios
# ──────────────────────────────────────────────

def cargar_beneficiarios(cursor, registros):
    """Inserta una fila por CIF único. Devuelve dict {cif_o_nombre: id_benef}.

    Recorre dos fuentes:
      1. Registros principales del dataset (todos los años y tipos).
      2. Municipios miembro de agrupaciones EELL 2025: son entidades locales
         individuales que solo aparecen dentro de municipios_agrupacion y no
         tienen registro propio en el dataset, por lo que hay que insertarlos
         aquí para poder referenciarlos con FK desde agrupacion_miembros.
    """
    vistos = {}  # cif_o_nombre → (cif, nombre, tipo_benef)

    # Fuente 1: registros principales
    for r in registros:
        cif   = r.get("cif") or None
        nombre = r["entidad"]
        tipo   = "asociacion" if r["tipo"] == "epa" else "entidad_local"
        clave  = cif if cif else f"__nombre__{nombre}"
        if clave not in vistos:
            vistos[clave] = (cif, nombre, tipo)

    # Fuente 2: municipios miembro de agrupaciones (EELL 2025)
    for r in registros:
        for mun in (r.get("municipios_agrupacion") or []):
            cif_mun    = mun.get("cif") or None
            nombre_mun = mun.get("nombre")
            if not nombre_mun:
                continue
            clave_mun = cif_mun if cif_mun else f"__nombre__{nombre_mun}"
            if clave_mun not in vistos:
                vistos[clave_mun] = (cif_mun, nombre_mun, "entidad_local")

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
            "INSERT INTO solicitudes (id_convoc, id_benef, num_expediente, puntuacion, estado, provincia, ccaa) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (id_convoc, id_benef, num_exp, puntuacion, estado,
             r.get("provincia") or None, r.get("ccaa") or None),
        )
        mapa_solic[i] = cursor.lastrowid
        insertadas += 1

    print(f"  Solicitudes: {insertadas} insertadas, {omitidas} ya existían")
    return mapa_solic


# ──────────────────────────────────────────────
# Paso 4: Concesiones
# ──────────────────────────────────────────────

def cargar_concesiones(cursor, registros, mapa_solic):
    """Inserta concesiones solo para registros con estado='concedida'.
    Devuelve dict {indice_registro: id_conces} para uso posterior en agrupaciones."""
    mapa_conces = {}
    insertadas  = 0
    omitidas    = 0

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
        fila = cursor.fetchone()
        if fila:
            mapa_conces[i] = fila["id_conces"]
            omitidas += 1
            continue

        cursor.execute(
            "INSERT INTO concesiones (id_solic, importe, linea, tramo) VALUES (%s, %s, %s, %s)",
            (id_solic, importe, linea, tramo),
        )
        mapa_conces[i] = cursor.lastrowid
        insertadas += 1

    print(f"  Concesiones: {insertadas} insertadas, {omitidas} ya existían")
    return mapa_conces


# ──────────────────────────────────────────────
# Paso 5: Agrupaciones + Miembros
# ──────────────────────────────────────────────

def cargar_agrupaciones(cursor, registros, mapa_benef, mapa_conces):
    """Inserta agrupaciones y sus municipios miembro para concesiones EELL 2025."""
    agrup_ins  = 0
    agrup_omit = 0
    miem_ins   = 0
    miem_omit  = 0

    for i, r in enumerate(registros):
        if not r.get("es_agrupacion") or r["estado"] != "concedida":
            continue

        id_conces = mapa_conces.get(i)
        if id_conces is None:
            continue

        muns = r.get("municipios_agrupacion") or []

        # Representante: el beneficiario principal del registro
        cif_rep = r.get("cif") or None
        clave_rep = cif_rep if cif_rep else f"__nombre__{r['entidad']}"
        id_represent = mapa_benef[clave_rep]

        # Insertar agrupación (o recuperar si ya existe)
        cursor.execute(
            "SELECT id_agrup FROM agrupaciones WHERE id_conces = %s", (id_conces,)
        )
        fila = cursor.fetchone()
        if fila:
            id_agrup = fila["id_agrup"]
            agrup_omit += 1
        else:
            cursor.execute(
                "INSERT INTO agrupaciones (id_conces, id_represent, num_municipios) "
                "VALUES (%s, %s, %s)",
                (id_conces, id_represent, len(muns)),
            )
            id_agrup = cursor.lastrowid
            agrup_ins += 1

        # Insertar miembros
        for mun in muns:
            cif_mun    = mun.get("cif") or None
            nombre_mun = mun.get("nombre")
            clave_mun  = cif_mun if cif_mun else f"__nombre__{nombre_mun}"
            id_benef_mun = mapa_benef.get(clave_mun)
            if id_benef_mun is None:
                print(f"  AVISO: miembro sin id_benef → {clave_mun}")
                continue

            cursor.execute(
                "SELECT id_agrupM FROM agrupacion_miembros "
                "WHERE id_agrup = %s AND id_benef = %s",
                (id_agrup, id_benef_mun),
            )
            if cursor.fetchone():
                miem_omit += 1
                continue

            cursor.execute(
                "INSERT INTO agrupacion_miembros (id_agrup, id_benef, importe_asignado) "
                "VALUES (%s, %s, %s)",
                (id_agrup, id_benef_mun, mun.get("importe_asignado") or 0.0),
            )
            miem_ins += 1

    print(f"  Agrupaciones:        {agrup_ins} insertadas, {agrup_omit} ya existían")
    print(f"  Agrupacion_miembros: {miem_ins} insertadas, {miem_omit} ya existían")


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
            print("\n[1/6] Convocatorias...")
            mapa_convoc = cargar_convocatorias(cursor, registros)

            print("[2/6] Beneficiarios...")
            mapa_benef = cargar_beneficiarios(cursor, registros)

            print("[3/6] Solicitudes...")
            mapa_solic = cargar_solicitudes(cursor, registros, mapa_convoc, mapa_benef)

            print("[4/6] Concesiones...")
            mapa_conces = cargar_concesiones(cursor, registros, mapa_solic)

            print("[5/6] Agrupaciones y miembros...")
            cargar_agrupaciones(cursor, registros, mapa_benef, mapa_conces)

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
