"""
bdns_client.py
Cliente para descargar convocatorias de la API BDNS (Base de Datos Nacional de Subvenciones).
Descarga convocatorias de protección animal y colonias felinas desde 2020 y las guarda en data/raw/
"""

import requests
import json
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"
FECHA_DESDE = "01/01/2020"
FECHA_HASTA = datetime.today().strftime("%d/%m/%Y")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw")

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
    y devuelve todos los resultados como lista.
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

        print(f"  Descargando página {page}...")
        response = requests.get(f"{BASE_URL}/convocatorias/busqueda", params=params)

        if response.status_code != 200:
            print(f"  Error {response.status_code} al consultar la API")
            break

        data = response.json()
        contenido = data.get("content", [])
        resultados.extend(contenido)

        # Si es la última página, paramos
        total_pages = data.get("totalPages", 1)
        if page >= total_pages - 1:
            break

        page += 1

    return resultados


def guardar_json(datos, nombre_archivo):
    """Guarda los datos en data/raw/ como archivo JSON."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ruta = os.path.join(OUTPUT_DIR, nombre_archivo)
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
        guardar_json(resultados, nombre_archivo)
    print("\nDescarga completada.")


if __name__ == "__main__":
    main()