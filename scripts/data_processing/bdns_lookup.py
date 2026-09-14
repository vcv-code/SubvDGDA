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


# La busqueda por descripcion de la API devuelve TAMBIEN cosas que no son las
# convocatorias de este proyecto: premios, certamenes artisticos y otras lineas
# de subvencion de la misma Direccion General. Comprobado el 13-09-2026, la
# consulta trae 8 resultados para "proteccion animal" y 5 para "colonias
# felinas", de los cuales solo 6 y 4 son los que interesan.
#
# Antes bastaba con que el titulo dijera "PROTECCI" para clasificarlo como
# `epa`, y eso hacia que dos convocatorias del MISMO ano cayeran en la misma
# clave del indice: la segunda pisaba a la primera sin avisar. Casos reales:
#
#   904804  PREMIOS NACIONALES A LA PROTECCION ANIMAL          -> pisaba la EPA 2026
#   797869  Subvenciones de concesion directa a las entidades
#           sin animo de lucro que gestionen centros y
#           refugios de proteccion animal                      -> pisaba la EPA 2024
#
# La 797869 es una subvencion de verdad, pero de concesion directa y de otra
# linea: no es la convocatoria en concurrencia que recoge esta web.
#
# El discriminante es el comienzo del titulo. Las de este proyecto se llaman
# siempre "Subvenciones a entidades ..."; las otras empiezan por "Premios",
# "N CERTAMEN" o "Subvenciones de concesion directa a las entidades ...".
_INICIO_ESPERADO = "SUBVENCIONES A ENTIDADES"


def _detectar_tipo(descripcion):
    """Detecta el tipo de convocatoria (`epa`, `eell` o `None`) por el titulo.

    Devuelve `None` para todo lo que no sea una convocatoria de las que recoge
    este proyecto. Preferir el `None` es deliberado: quien llama usa entonces
    los diccionarios `_FECHAS` / `_TITULO` como respaldo, que es un fallo
    visible y recuperable; clasificar de mas escribe datos equivocados en la
    base sin que nadie se entere.

    Logica espejo de `docker/cron/scripts/check_bdns.py:detectar_tipo()`. Se
    mantiene duplicada de forma intencionada: el pipeline de carga y el cron
    se ejecutan en contextos distintos (procesos, contenedores y momentos
    diferentes) y no comparten codigo. Si se cambia aqui, hay que cambiarla
    alli; hay un test que comprueba que las dos coinciden.
    """
    desc = (descripcion or "").upper()
    if _INICIO_ESPERADO not in desc:
        return None
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

            # Dos convocatorias distintas en la misma clave significa que el
            # detector se ha quedado corto. Antes la segunda pisaba a la
            # primera en silencio y la carga seguia con el dato equivocado.
            # Ahora se avisa y se conserva la PRIMERA: el orden de la API es
            # por numero ascendente, y la convocatoria del ano suele publicarse
            # antes que los premios o los certamenes que la acompanan.
            anterior = indice.get((anio, tipo))
            if anterior is not None:
                print(
                    f"  AVISO: {anio}/{tipo} ya estaba asignada a la convocatoria "
                    f"{anterior['num_convoc']} ({anterior['titulo'][:60]}); se "
                    f"DESCARTA {r['numeroConvocatoria']} ({(r.get('descripcion') or '')[:60]}). "
                    "Revisa `_detectar_tipo`."
                )
                continue

            indice[(anio, tipo)] = {
                "num_convoc": str(r["numeroConvocatoria"]),
                "titulo": r.get("descripcion") or "",
                "fecha_convocatoria": fecha,
                "bdns_id": r.get("id"),
            }

    return indice
