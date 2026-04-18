"""
bdns_client.py

Cliente sencillo para descargar convocatorias de la API BDNS
(Base de Datos Nacional de Subvenciones).

Este script:
1. Consulta la API BDNS buscando convocatorias relacionadas con bienestar animal.
2. Descarga todas las páginas de resultados (paginación).
3. Guarda los resultados en archivos JSON dentro de data/raw/.
4. Añade la fecha al archivo para mantener histórico de descargas.
5. Elimina duplicados básicos por numeroConvocatoria.
6. Añade el campo anio_convocatoria para facilitar análisis posteriores.
"""

import requests
import json
import os
from datetime import datetime


# CONFIGURACIÓN GENERAL

BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"

FECHA_DESDE = "01/01/2020"
FECHA_HASTA = datetime.today().strftime("%d/%m/%Y")

# Fecha actual para incluirla en el nombre del archivo
HOY = datetime.today().strftime("%Y-%m-%d")

# Carpeta donde se guardarán los archivos descargados
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw", "convBDNS")


# Búsquedas que queremos realizar en la API
BUSQUEDAS = [
    {
        "descripcion": "protección animal",
        "nombre_archivo": "convocatorias_proteccion_animal.json"
    },
    {
        "descripcion": "colonias felinas",
        "nombre_archivo": "convocatorias_colonias_felinas.json"
    }
]


def buscar_convocatorias(descripcion):
    """
    Llama al endpoint /convocatorias/busqueda con paginación
    y devuelve todos los resultados encontrados.
    """

    resultados = []
    page = 0
    page_size = 50

    while True:

        params = {
            "page": page,
            "pageSize": page_size,
            "order": "numeroConvocatoria",
            "direccion": "asc",
            "vpd": "GE",
            "descripcion": descripcion,
            "descripcionTipoBusqueda": 0,
            "mrr": "false",
            "contribucion": "false",
            "fechaDesde": FECHA_DESDE,
            "fechaHasta": FECHA_HASTA,
            "tipoAdministracion": "C"
        }

        print(f"  Descargando página {page + 1}...")

        # Llamada a la API con control de errores
        try:
            response = requests.get(
                f"{BASE_URL}/convocatorias/busqueda",
                params=params,
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            print(f"  Error de conexión con la API: {e}")
            break

        if response.status_code != 200:
            print(f"  Error {response.status_code} al consultar la API")
            break

        # Convertimos la respuesta a JSON
        try:
            data = response.json()
        except ValueError:
            print("  Error al interpretar la respuesta JSON")
            break

        contenido = data.get("content", [])
        resultados.extend(contenido)

        # Control de paginación
        total_pages = data.get("totalPages", 1)

        if page >= total_pages - 1:
            break

        page += 1

    return resultados


def eliminar_duplicados(convocatorias):
    """
    Elimina convocatorias duplicadas usando numeroConvocatoria.
    """

    vistas = set()
    resultados = []

    for c in convocatorias:
        numero = c.get("numeroConvocatoria")

        if numero not in vistas:
            vistas.add(numero)
            resultados.append(c)

    return resultados


def añadir_anio_convocatoria(convocatorias):
    """
    Añade el campo anio_convocatoria a cada convocatoria
    a partir de la fechaRecepcion.
    """

    for c in convocatorias:

        fecha = c.get("fechaRecepcion")

        if fecha:
            try:
                anio = datetime.strptime(fecha, "%Y-%m-%d").year
                c["anio_convocatoria"] = anio
            except ValueError:
                c["anio_convocatoria"] = None
        else:
            c["anio_convocatoria"] = None

    return convocatorias


def guardar_json(datos, nombre_archivo):
    """
    Guarda los datos en data/raw/.
    El nombre del archivo incluye la fecha de descarga.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    nombre_con_fecha = f"{HOY}_{nombre_archivo}"
    ruta = os.path.join(OUTPUT_DIR, nombre_con_fecha)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"  Guardado en {ruta} ({len(datos)} convocatorias)")


def main():

    for busqueda in BUSQUEDAS:

        descripcion = busqueda["descripcion"]
        nombre_archivo = busqueda["nombre_archivo"]

        print(f"\nBuscando: '{descripcion}'...")

        resultados = buscar_convocatorias(descripcion)

        print(f"  Total encontradas: {len(resultados)}")

        # Eliminamos duplicados
        resultados = eliminar_duplicados(resultados)
        print(f"  Tras eliminar duplicados: {len(resultados)}")

        # FILTRADO (ANTES de añadir campos)
        resultados = filtrar_convocatorias_validas(resultados)
        print(f"  Tras filtrar: {len(resultados)}")

        # Añadimos el año
        resultados = añadir_anio_convocatoria(resultados)

        guardar_json(resultados, nombre_archivo)

    print("\nDescarga completada.")

def filtrar_convocatorias_validas(convocatorias):
    resultados = []

    for c in convocatorias:
        nivel3 = (c.get("nivel3") or "").upper()
        descripcion = (c.get("descripcion") or "").upper()

        # ✔ solo DGDA
        if "DERECHOS DE LOS ANIMALES" not in nivel3:
            continue

        # ✔ solo subvenciones reales (opcional pero recomendable)
        if "SUBVENCIONES" not in descripcion:
            continue

        resultados.append(c)

    return resultados
if __name__ == "__main__":
    main()