"""
bdns_lookup.py
==============
Lee los snapshots de la API BDNS guardados en `data/raw/convBDNS/` y devuelve
un indice por `(anio, tipo)` con los datos oficiales de cada convocatoria DGDA.

Para cada patron de fichero (proteccion_animal, colonias_felinas) se usa el
snapshot mas reciente segun la fecha del prefijo del nombre, que tiene formato
`YYYY-MM-DD_*.json`. Como el orden alfabetico coincide con el cronologico,
basta con `sorted()` y coger el ultimo.

Se usa en `cargar_dataset.py` como fuente oficial de:
  - num_convoc (numero de convocatoria en BDNS)
  - fecha_convocatoria
  - titulo_convoc

Si BDNS no tiene datos para una `(anio, tipo)` concreta (caso tipico: anos
futuros antes de que la DGDA publique la convocatoria), el llamador usa los
diccionarios hardcodeados `_FECHAS` y `_TITULO` de `cargar_dataset.py` como
fallback.
"""

import glob
import json
import os
from datetime import date


BDNS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "convBDNS")
)

PATRONES_BDNS = [
    "*_convocatorias_proteccion_animal.json",
    "*_convocatorias_colonias_felinas.json",
]


def _detectar_tipo(descripcion):
    """Detecta el tipo de convocatoria (`epa`, `eell` o `None`) por palabras clave del titulo.

    Logica espejo de `docker/cron/scripts/check_bdns.py:detectar_tipo()`. Se
    mantiene duplicada de forma intencionada: el pipeline de carga y el cron
    se ejecutan en contextos distintos (procesos, contenedores y momentos
    diferentes) y no comparten codigo.
    """
    desc = (descripcion or "").upper()
    if "ENTIDADES LOCALES" in desc or "EELL" in desc:
        return "eell"
    if "ENTIDADES PRIVADAS" in desc or "ASOCIACIONES" in desc or "PROTECCI" in desc:
        return "epa"
    return None


def _snapshot_mas_reciente(patron):
    """Devuelve la ruta al snapshot mas reciente que coincida con `patron`, o `None`."""
    candidatos = sorted(glob.glob(os.path.join(BDNS_DIR, patron)))
    return candidatos[-1] if candidatos else None


def cargar_indice_bdns():
    """Devuelve `{(anio, tipo): {num_convoc, titulo, fecha_convocatoria, bdns_id}}`.

    Lee los snapshots mas recientes de cada patron de fichero, detecta el tipo
    por palabras clave y agrega los campos relevantes para la carga del dataset.
    Si una `(anio, tipo)` aparece duplicada (poco probable) se queda con la
    ultima leida.
    """
    indice = {}

    for patron in PATRONES_BDNS:
        ruta = _snapshot_mas_reciente(patron)
        if ruta is None:
            continue

        with open(ruta, encoding="utf-8") as f:
            registros = json.load(f)

        for r in registros:
            tipo = _detectar_tipo(r.get("descripcion"))
            if tipo is None:
                continue

            anio = r.get("anio_convocatoria")
            if anio is None:
                continue

            try:
                fecha = (
                    date.fromisoformat(r["fechaRecepcion"])
                    if r.get("fechaRecepcion")
                    else None
                )
            except ValueError:
                fecha = None

            indice[(anio, tipo)] = {
                "num_convoc": str(r["numeroConvocatoria"]),
                "titulo": r.get("descripcion") or "",
                "fecha_convocatoria": fecha,
                "bdns_id": r.get("id"),
            }

    return indice
