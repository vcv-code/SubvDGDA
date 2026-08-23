"""
unificar_datasets.py
====================
Carga todos los JSON procesados de EPAs y EELL,
normaliza campos, añade 'tipo', elimina duplicados
y genera data/final/dataset_unificado.json.

Esquema final de cada registro:
{
    "anio":          int,
    "tipo":          "epa" | "eell",
    "num_expediente": str,
    "entidad":       str | None,
    "cif":           str | None,
    "puntuacion":    float | None,
    "importe":       float,        # 0.0 si no consta
    "estado":          str,          # concedida | no_beneficiaria | excluida | desistida
    "tramo":           int | None,  # 1, 2 o 3 solo para EELL 2025 concedidas; None en el resto
    "causa_exclusion": str | None,  # código(s) de causa, solo en excluidas EELL; None en el resto
    "provincia":       str | None,  # derivada del CIF para EELL; None para EPA
    "ccaa":            str | None,  # derivada del CIF para EELL; None para EPA
    "periodo_meses":   int,         # duración del periodo subvencionable
                                    # EPA: 6 (2023/2024) o 12 (resto); EELL: siempre 12
    "es_agrupacion":   bool,        # True solo en EELL 2025 concedidas como agrupación; False en el resto
    "municipios_agrupacion": list | None,
                             # Solo cuando es_agrupacion=True.
                             # Lista de {cif, nombre, importe_asignado} con todos los
                             # municipios miembro, incluido el representante.
                             # None en el resto de registros.
}

Notas sobre el periodo subvencionable:
  EPA  2021, 2022, 2025 → anual (12 meses)
  EPA  2023, 2024       → semestral (6 meses)
  EELL 2023             → semestral (6 meses): oct 2023 a mar 2024
  EELL 2024, 2025       → anual (12 meses)
  Tenerlo en cuenta al comparar importes entre años.

  Ojo además con el AÑO que financia cada convocatoria, que no es el suyo: las
  EPA de 2021-2024 y todas las EELL pagan gastos del año siguiente. El detalle,
  con la cita del BOE de cada una, está en `_PERIODO_SUBVENCIONABLE`
  (scripts/data_processing/cargar_dataset.py).

Notas sobre EELL 2023/2024 (PDF):
  El parser PDF devuelve todos los registros con estado='concedida'.
  Los que tienen importe=0 se reclasifican como 'no_beneficiaria'
  (superaron el baremo pero no recibieron fondos al quedar fuera del cupo).
  Los realmente excluidos (ANEXO III) no se capturan de forma fiable
  desde el PDF — para tenerlos habría que re-parsear o añadirlos manualmente.
"""

import json
import os
import re
from collections import Counter


# Algunos parsers (PDF y XML) generan secuencias "uXXXX" sin barra invertida
# para caracteres acentuados (p.ej. "PUu00C7OL" → "PUÇOL", "u00D3" → "Ó").
# Solo aplicamos el arreglo en el rango Latin-1 Suplemento (U+00A0–U+00FF)
# para evitar tocar texto legitimo que contenga la letra "u" seguida de hex.
_UNICODE_ESCAPE_RX = re.compile(r'u([0-9A-Fa-f]{4})')


def _arreglar_escapes_unicode(texto):
    def repl(m):
        code = int(m.group(1), 16)
        if 0x00A0 <= code <= 0x00FF:
            return chr(code)
        return m.group(0)
    return _UNICODE_ESCAPE_RX.sub(repl, texto)


# =========================
# MAPEO PROVINCIA → CCAA
# Basado en códigos INE de provincia (2 dígitos).
# Se extrae de las posiciones 1-2 del CIF de entidades locales
# (formato: letra_tipo + 2_dígitos_provincia + resto).
# =========================

# Entidades con CIF de código de provincia no estándar (mancomunidades supra-municipales,
# consells comarcals, ciudades autónomas). Se identifican por CIF completo.
# Mancomunidades que cruzan varias provincias llevan provincia=None y solo ccaa.
_CIF_OVERRIDE = {
    "P5606301I": (None,       "Extremadura"),               # Mancomunidad Cijara (Cáceres/Badajoz)
    "P5612701B": ("Badajoz",  "Extremadura"),               # Mancomunidad Siberia
    "P5390001E": ("Alicante", "Comunidad Valenciana"),      # Mancomunidad L'Alacantí
    "P6400601H": ("Córdoba",  "Andalucía"),                 # Mancomunidad Los Pedroches
    "P6700008C": ("Girona",   "Cataluña"),                  # Consell Comarcal Alt Empordà
    "P6700010I": ("Girona",   "Cataluña"),                  # Consell Comarcal Pla de l'Estany
    "S7900010E": ("Melilla",  "Ciudad Autónoma de Melilla"),# Ciudad Autónoma de Melilla
    "G79458618": ("Madrid",   "Comunidad de Madrid"),       # Mancomunidad El Molar/S.Agustín/Guadalix
}

_PROVINCIA_CCAA = {
    "01": ("Álava",                    "País Vasco"),
    "02": ("Albacete",                 "Castilla-La Mancha"),
    "03": ("Alicante",                 "Comunidad Valenciana"),
    "04": ("Almería",                  "Andalucía"),
    "05": ("Ávila",                    "Castilla y León"),
    "06": ("Badajoz",                  "Extremadura"),
    "07": ("Illes Balears",            "Illes Balears"),
    "08": ("Barcelona",                "Cataluña"),
    "09": ("Burgos",                   "Castilla y León"),
    "10": ("Cáceres",                  "Extremadura"),
    "11": ("Cádiz",                    "Andalucía"),
    "12": ("Castellón",                "Comunidad Valenciana"),
    "13": ("Ciudad Real",              "Castilla-La Mancha"),
    "14": ("Córdoba",                  "Andalucía"),
    "15": ("A Coruña",                 "Galicia"),
    "16": ("Cuenca",                   "Castilla-La Mancha"),
    "17": ("Girona",                   "Cataluña"),
    "18": ("Granada",                  "Andalucía"),
    "19": ("Guadalajara",              "Castilla-La Mancha"),
    "20": ("Gipuzkoa",                 "País Vasco"),
    "21": ("Huelva",                   "Andalucía"),
    "22": ("Huesca",                   "Aragón"),
    "23": ("Jaén",                     "Andalucía"),
    "24": ("León",                     "Castilla y León"),
    "25": ("Lleida",                   "Cataluña"),
    "26": ("La Rioja",                 "La Rioja"),
    "27": ("Lugo",                     "Galicia"),
    "28": ("Madrid",                   "Comunidad de Madrid"),
    "29": ("Málaga",                   "Andalucía"),
    "30": ("Murcia",                   "Región de Murcia"),
    "31": ("Navarra",                  "Comunidad Foral de Navarra"),
    "32": ("Ourense",                  "Galicia"),
    "33": ("Asturias",                 "Principado de Asturias"),
    "34": ("Palencia",                 "Castilla y León"),
    "35": ("Las Palmas",               "Canarias"),
    "36": ("Pontevedra",               "Galicia"),
    "37": ("Salamanca",                "Castilla y León"),
    "38": ("Santa Cruz de Tenerife",   "Canarias"),
    "39": ("Cantabria",                "Cantabria"),
    "40": ("Segovia",                  "Castilla y León"),
    "41": ("Sevilla",                  "Andalucía"),
    "42": ("Soria",                    "Castilla y León"),
    "43": ("Tarragona",                "Cataluña"),
    "44": ("Teruel",                   "Aragón"),
    "45": ("Toledo",                   "Castilla-La Mancha"),
    "46": ("Valencia",                 "Comunidad Valenciana"),
    "47": ("Valladolid",               "Castilla y León"),
    "48": ("Bizkaia",                  "País Vasco"),
    "49": ("Zamora",                   "Castilla y León"),
    "50": ("Zaragoza",                 "Aragón"),
    "51": ("Ceuta",                    "Ciudad Autónoma de Ceuta"),
    "52": ("Melilla",                  "Ciudad Autónoma de Melilla"),
}


def provincia_ccaa_de_cif(cif):
    """
    Extrae provincia y CCAA del CIF de una entidad local.
    El CIF de entidades locales tiene el formato:
      letra_tipo (1 car) + código_provincia (2 dígitos) + resto
    Primero comprueba el diccionario de overrides manuales (mancomunidades
    supra-municipales, consells comarcals, ciudades autónomas).
    Devuelve (provincia, ccaa) o (None, None) si no se puede derivar.
    """
    if not cif or len(cif) < 3:
        return None, None
    override = _CIF_OVERRIDE.get(cif)
    if override:
        return override[0], override[1]
    codigo = cif[1:3]
    entrada = _PROVINCIA_CCAA.get(codigo)
    if entrada:
        return entrada[0], entrada[1]
    return None, None


# =========================
# LIMPIEZA DE CAMPOS
# =========================

def limpiar_cif(valor):
    if valor is None:
        return None
    v = str(valor).strip()
    if v == "" or v.lower() == "none" or v in ["–", "-"]:
        return None
    return v


def limpiar_importe(valor):
    if valor is None or valor == "":
        return 0.0
    try:
        return float(valor)
    except:
        return 0.0


def limpiar_estado(valor):
    if valor is None:
        return None
    v = str(valor).strip().lower()
    if v == "" or v == "none":
        return None
    return v


def limpiar_puntuacion(valor):
    if valor is None:
        return None
    try:
        return float(valor)
    except:
        return None


def limpiar_entidad(valor):
    if valor is None:
        return None
    # rstrip('.') quita el punto final tipográfico que el BOE añade a casi todos los
    # nombres en sus tablas. No hay nombres con puntos solo en medio (verificado en
    # el dataset de junio 2026: 2478/3103 con punto final, 0 con punto solo intermedio).
    v = str(valor).strip().rstrip('.').strip()
    if v == "" or v.lower() == "none":
        return None
    return _arreglar_escapes_unicode(v)


# =========================
# CORRECCIONES DE ORIGEN
# =========================
# Erratas del BOE verificadas una a una contra fuentes oficiales. Se corrigen
# aquí, en el único punto por el que pasan todos los registros, y NO en la base
# de datos, para que sobrevivan a un `reset-db` y a cualquier recarga.
#
# El criterio es el mismo que en `resolver_anio_epa`: solo se toca lo que está
# PROBADO. Un CIF sin autoridad para corregirlo sería inventar, y la web se
# apoya en reproducir fielmente lo publicado.

# CIF erróneo -> CIF bueno. Sin esta tabla la entidad aparece partida en dos
# fichas y su histórico se ve incompleto.
CIF_CORREGIDO = {
    # Transposición de dos dígitos en el BOE de 2024 (…37041 -> …34071). El CIF
    # bueno es el de 2022, 2023 y 2025 —tres años frente a uno— y lo confirma la
    # concesión de 2022 publicada en la BDNS (convocatoria 645245).
    "G16734071": "G16737041",
    # Rectificación oficial: BOE-A-2023-13752, «Corrección de errores de la
    # Resolución de 12 de diciembre de 2022 [...] Convocatoria 2022», que dice
    # literalmente que donde pone G72307358 debe poner G72296254.
    "G72307358": "G72296254",
    # El BOE de 2024 la publica como B54999156 y el de 2025 como G54999156. La
    # entidad está inscrita en el Registro de Asociaciones de Alicante (consulta
    # pública del Ministerio del Interior), y una asociación no puede llevar un
    # NIF con «B», que es de sociedad limitada. La letra buena es la G.
    "B54999156": "G54999156",
    # ATENCIÓN: el único de la tabla NO verificado contra una fuente externa.
    # G56705338 (2024) frente a G56725328 (2025): ambos validan, difieren en dos
    # posiciones y ninguno aparece en la web asociado a entidad alguna. Se adopta
    # el de 2025 por ser la publicación más reciente de la misma autoridad.
    # Decisión consciente, revisable si aparece una fuente mejor.
    "G56705338": "G56725328",
}

# CIF -> nombre bueno. Dos casos distintos:
#   - Municipios cuyo NOMBRE está mal en el BOE (el CIF sí es correcto, y por
#     eso la provincia y las estadísticas ya salían bien). Verificados contra
#     las webs municipales y contra el diccionario de municipios del INE.
#   - Entidades unificadas arriba, que traían dos grafías: se fija la mayoritaria
#     para que la ficha no cambie de nombre según el año.
NOMBRE_CORREGIDO = {
    "P4608700C": "AYUNTAMIENTO DE CARLET",                 # el BOE dice «Casavieja»
    "P1303100J": "AYUNTAMIENTO DE CARRIÓN DE CALATRAVA",   # el BOE dice «Castilforte»
    "G16737041": "ASSOCIACIÓ GAT I CUA",                   # grafía valenciana correcta
    "G72296254": 'ASOCIACIÓN "GATOS DE EL PUERTO"',        # 3 años frente a 1
}

# (nombre, año) -> CIF. Para registros que salieron en el BOE SIN CIF y cuya
# entidad sí lo tiene en otros años. Va con el año para no asignar a ciegas un
# CIF a cualquier homónimo futuro.
CIF_AUSENTE = {
    # Confirmado además por la BDNS, que registra la concesión de 2022 de esta
    # asociación con ese NIF.
    ("LAS ALMAS DE COCOA", 2021): "G67811000",
}

# Cómo comprobar un NIF dudoso, por orden de solidez:
#   1. Corrección de errores en el BOE (es lo que zanjó Gatos de El Puerto).
#   2. BDNS: concesiones/busqueda?nifCif=<CIF>. Solo cubre CONCEDIDAS, y de
#      nuestras convocatorias solo tiene cargada la de 2022 (645245).
#   3. Consulta pública de asociaciones del Ministerio del Interior: no publica
#      el NIF, pero sí confirma que la entidad es una asociación —y por tanto
#      que su NIF empieza por G—, que es lo que resolvió Torrevieja.
#   4. La propia entidad: muchas protectoras publican su CIF para donativos.


def corregir_identidad(cif, nombre, anio):
    """Aplica las correcciones de origen. Devuelve (cif, nombre, corregido)."""
    original = (cif, nombre)

    if cif is None and nombre is not None:
        cif = CIF_AUSENTE.get((nombre, anio))

    if cif is not None:
        cif = CIF_CORREGIDO.get(cif, cif)
        nombre = NOMBRE_CORREGIDO.get(cif, nombre)

    return cif, nombre, (cif, nombre) != original


# =========================
# NORMALIZACIÓN DE ESTADO EELL
# Los JSON de PDF tienen solo 'concedida'.
# Los que tienen importe=0 se reclasifican como 'no_beneficiaria'.
# =========================

def normalizar_estado_eell(estado, importe):
    if estado == "concedida" and (importe is None or importe == 0.0):
        return "no_beneficiaria"
    return estado


# =========================
# NORMALIZACIÓN DE ESTADO EPA
# El BOE llama "denegadas" a dos realidades distintas según el año:
#   - 2021-2023: son exclusiones formales con causa (→ 'excluida').
#     En esos años todas las protectoras recibían algo; las que no,
#     tenían una causa administrativa explícita.
#   - 2024-2025: son no beneficiarias por puntuación insuficiente (→ 'no_beneficiaria').
#     A partir de 2024 el cupo presupuestario no alcanza a todas.
# Con esto 'denegada' desaparece del dataset final.
# =========================

def normalizar_estado_epa(estado, anio):
    if estado == "denegada":
        return "excluida" if anio <= 2023 else "no_beneficiaria"
    return estado


# =========================
# CARGADORES POR TIPO
# =========================

def indexar_solicitudes_epa(datos_por_anio):
    """
    Índice {anio_fichero: {(num_expediente, cif), ...}} usado para detectar
    resoluciones tardías. Ver `resolver_anio_epa`.
    """
    indice = {}
    for anio_fichero, data in datos_por_anio.items():
        indice[anio_fichero] = {
            (str(item.get("num_expediente") or "").strip(),
             str(item.get("cif") or "").strip())
            for item in data
        }
    return indice


def resolver_anio_epa(item, anio_fichero, indice):
    """
    Devuelve el año de convocatoria al que pertenece un registro EPA.

    Por defecto es el año del fichero fuente (el BOE en que se publicó). La
    excepción son las RESOLUCIONES TARDÍAS: una solicitud presentada en el año N
    cuya resolución no sale hasta el BOE del año N+1. En ese caso el JSON de
    origen trae `anio` = N (el año codificado en el número de expediente) y hay
    que atribuir el registro —y su importe— a la convocatoria N, no al N+1.

    Solo se reatribuye cuando está PROBADO que es la misma solicitud: el mismo
    número de expediente Y el mismo CIF tienen que existir también en el fichero
    del año declarado. Esa condición deja fuera los dos falsos positivos:

      - SUBV2022021: en el BOE de 2021 es Amores Perros Cádiz (G01779131) y en
        el de 2022 es Can Terrassa (G66561812). El BOE reutilizó el número para
        otra entidad; el CIF no coincide, así que cada una se queda en su año.
      - SUBV2032021: trae `anio` 2032 por una errata del número de expediente.
        No hay fichero de 2032, así que se queda en el año de su BOE.

    Sin esta comprobación, reatribuir por el `anio` del JSON volvería a colapsar
    registros distintos bajo la misma clave de deduplicación.
    """
    anio_declarado = item.get("anio")
    if anio_declarado is None or anio_declarado == anio_fichero:
        return anio_fichero

    clave = (str(item.get("num_expediente") or "").strip(),
             str(item.get("cif") or "").strip())
    if clave in indice.get(anio_declarado, ()):
        return anio_declarado

    return anio_fichero


def cargar_epas(archivos):
    """
    Carga registros EPA desde sus JSON.
    Campos origen: anio, num_expediente, entidad, cif, puntuacion, importe, estado
    """
    registros = []
    contador_sin_exp = {}   # {anio: contador} para IDs sintéticos únicos

    # Pre-lectura de todos los ficheros: `resolver_anio_epa` necesita saber qué
    # expedientes hay en los demás años para detectar resoluciones tardías.
    datos_por_anio = {}
    for ruta, anio_fallback in archivos:
        if not os.path.exists(ruta):
            print(f"  AVISO: no encontrado → {ruta}")
            continue
        datos_por_anio[anio_fallback] = json.load(open(ruta, encoding="utf-8"))

    indice = indexar_solicitudes_epa(datos_por_anio)

    for ruta, anio_fallback in archivos:
        if anio_fallback not in datos_por_anio:
            continue

        data = datos_por_anio[anio_fallback]

        sin_exp_en_archivo = 0
        reatribuidos_en_archivo = 0
        corregidos_en_archivo = 0
        for item in data:
            # Saltar filas de totales parseadas como entidades
            # (ej: la fila "TOTAL" de la tabla de importes en EPA 2024 y 2025)
            cif_check = str(item.get("cif", "") or "").strip().lower().rstrip(".")
            if cif_check in ("total", "totales"):
                continue

            expediente_raw = item.get("num_expediente")

            # Registros sin num_expediente (ej: excluidas EPA 2025 que el BOE no numera):
            # se les asigna un ID sintético único para no perderlos.
            if not expediente_raw:
                contador_sin_exp[anio_fallback] = contador_sin_exp.get(anio_fallback, 0) + 1
                expediente_raw = f"SIN_EXP_{anio_fallback}_{contador_sin_exp[anio_fallback]:03d}"
                sin_exp_en_archivo += 1

            importe = limpiar_importe(item.get("importe"))
            estado = limpiar_estado(item.get("estado"))

            # Normalizar: campo puede llamarse 'puntuacion'
            puntuacion = limpiar_puntuacion(
                item.get("puntuacion") or item.get("puntos")
            )

            # Año de convocatoria: el del fichero salvo resolución tardía
            # comprobada (mismo expediente y mismo CIF en el año declarado).
            anio_item = resolver_anio_epa(item, anio_fallback, indice)
            if anio_item != anio_fallback:
                reatribuidos_en_archivo += 1

            estado = normalizar_estado_epa(estado, anio_item)

            cif_epa, entidad_epa, hubo_correccion = corregir_identidad(
                limpiar_cif(item.get("cif")),
                limpiar_entidad(item.get("entidad")),
                anio_item,
            )
            if hubo_correccion:
                corregidos_en_archivo += 1

            registros.append({
                "anio": anio_item,
                "tipo": "epa",
                "num_expediente": str(expediente_raw).strip(),
                "entidad": entidad_epa,
                "cif": cif_epa,
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "linea": item.get("linea") or None,
                "tramo": None,           # las EPAs no tienen tramo
                # Causa de exclusión capturada del BOE: código(s) en 2022-2025,
                # texto literal en 2021 (ese anexo no usa códigos). None en el resto.
                "causa_exclusion": (str(item["causa_exclusion"]).strip()
                                    if item.get("causa_exclusion") else None),
                # La provincia de una asociación NO se puede sacar de su CIF, y no
                # es una precaución teórica: ASSOCIACIÓ GAT I CUA (G16737041) está
                # en Cruïlles, Monells i Sant Sadurní de l\'Heura (Girona, 17) y
                # esos dos dígitos dicen 16, que es Cuenca. En la mayoría de las
                # protectoras del dataset ni siquiera son un código de provincia
                # válido (G54…, G56…, G72…: series nacionales por encima de 52).
                # Derivarla publicaría ubicaciones falsas. Hace falta otra fuente.
                "provincia": None,
                "ccaa": None,
                # Propiedad de la convocatoria, por eso sigue a anio_item
                # (no al fichero) en las resoluciones tardías reatribuidas.
                "periodo_meses": 6 if anio_item in (2023, 2024) else 12,
                "es_agrupacion": False,
                "municipios_agrupacion": None,
            })

        aviso_sin_exp = f" ({sin_exp_en_archivo} sin expediente → ID sintético)" if sin_exp_en_archivo else ""
        aviso_reatrib = f" ({reatribuidos_en_archivo} resolución/es tardía/s reatribuida/s a su convocatoria)" if reatribuidos_en_archivo else ""
        aviso_correc = f" ({corregidos_en_archivo} errata/s de origen corregida/s)" if corregidos_en_archivo else ""
        print(f"  EPA {anio_fallback}: {len(data)} registros cargados desde {os.path.basename(ruta)}{aviso_sin_exp}{aviso_reatrib}{aviso_correc}")

    return registros


def cargar_eell(archivos):
    """
    Carga registros EELL desde sus JSON.
    Campos origen: num_expediente, entidad, cif, puntos, importe, estado
    El campo 'anio' no está en los JSON de PDF — se pasa como parámetro.
    El campo '_meta' se descarta.
    """
    registros = []

    for ruta, anio in archivos:
        corregidos_en_archivo = 0
        if not os.path.exists(ruta):
            print(f"  AVISO: no encontrado → {ruta}")
            continue

        data = json.load(open(ruta, encoding="utf-8"))

        for item in data:
            if not item.get("num_expediente"):
                continue

            importe = limpiar_importe(item.get("importe"))
            estado_raw = limpiar_estado(item.get("estado"))
            estado = normalizar_estado_eell(estado_raw, importe)

            # Normalizar: campo puede llamarse 'puntos' o 'puntuacion'
            puntuacion = limpiar_puntuacion(
                item.get("puntuacion") or item.get("puntos")
            )

            # tramo: solo presente en EELL 2025 concedidas; None en el resto
            tramo_raw = item.get("tramo")
            tramo = int(tramo_raw) if tramo_raw is not None else None

            causa_raw = item.get("causa_exclusion")
            causa = str(causa_raw).strip() if causa_raw else None

            cif_limpio, entidad_eell, hubo_correccion = corregir_identidad(
                limpiar_cif(item.get("cif")),
                limpiar_entidad(item.get("entidad")),
                anio,
            )
            if hubo_correccion:
                corregidos_en_archivo += 1
            # La provincia se deriva DESPUÉS de corregir, no antes.
            provincia, ccaa = provincia_ccaa_de_cif(cif_limpio)

            registros.append({
                "anio": anio,
                "tipo": "eell",
                "num_expediente": str(item["num_expediente"]).strip(),
                "entidad": entidad_eell,
                "cif": cif_limpio,
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "tramo": tramo,
                "causa_exclusion": causa,
                "provincia": provincia,
                "ccaa": ccaa,
                # La EELL de 2023 NO fue anual: su extracto en el BOE fija el
                # periodo «entre el 1 de octubre de 2023 y el 31 de marzo del
                # año 2024», seis meses. El resto sí son anuales.
                "periodo_meses": 6 if anio == 2023 else 12,
                "es_agrupacion": bool(item.get("es_agrupacion", False)),
                "municipios_agrupacion": item.get("municipios_agrupacion"),
                # _meta se descarta intencionalmente
            })

        aviso_correc = f" ({corregidos_en_archivo} errata/s de origen corregida/s)" if corregidos_en_archivo else ""
        print(f"  EELL {anio}: {len(data)} registros cargados desde {os.path.basename(ruta)}{aviso_correc}")

    return registros


# =========================
# VALIDACIÓN
# =========================

def validar_y_mostrar(final):
    print("\n========== VALIDACIÓN FINAL ==========")
    print(f"Total registros: {len(final)}")

    print("\nPor año:")
    for anio, n in sorted(Counter(r["anio"] for r in final).items()):
        print(f"  {anio}: {n}")

    print("\nPor tipo:")
    for tipo, n in sorted(Counter(r["tipo"] for r in final).items()):
        print(f"  {tipo}: {n}")

    print("\nPor estado:")
    for estado, n in sorted(Counter(r["estado"] for r in final).items(), key=lambda x: -x[1]):
        print(f"  {estado}: {n}")

    print("\nPor año y tipo:")
    combo = Counter((r["anio"], r["tipo"]) for r in final)
    for (anio, tipo), n in sorted(combo.items()):
        print(f"  {anio} / {tipo}: {n}")

    print("\nCalidad de datos:")
    sin_cif = sum(1 for r in final if r["cif"] is None)
    sin_entidad = sum(1 for r in final if r["entidad"] is None)
    sin_importe = sum(1 for r in final if r["importe"] == 0.0)
    sin_estado = sum(1 for r in final if r["estado"] is None)
    sin_puntuacion = sum(1 for r in final if r["puntuacion"] is None)
    eell_sin_provincia = sum(1 for r in final if r["tipo"] == "eell" and r["provincia"] is None)
    print(f"  Sin CIF:               {sin_cif}")
    print(f"  Sin entidad:           {sin_entidad}")
    print(f"  Importe = 0:           {sin_importe}")
    print(f"  Sin estado:            {sin_estado}")
    print(f"  Sin puntuación:        {sin_puntuacion}")
    print(f"  EELL sin provincia:    {eell_sin_provincia}")

    agrupaciones = [r for r in final if r.get("es_agrupacion")]
    if agrupaciones:
        total_muns = sum(len(r["municipios_agrupacion"]) for r in agrupaciones if r["municipios_agrupacion"])
        print(f"\nAgrupaciones EELL 2025:")
        print(f"  Nº agrupaciones:       {len(agrupaciones)}")
        print(f"  Nº municipios miembro: {total_muns}")
        for r in sorted(agrupaciones, key=lambda x: x.get("tramo", 0)):
            n = len(r["municipios_agrupacion"]) if r["municipios_agrupacion"] else 0
            print(f"    Tramo {r['tramo']} | {r['entidad'][:55]:55s} | {n} municipios")

    print("\nComparación con Excel de referencia (JSON procesados, antes de deduplicación):")
    print("  EPAs: 2021=328, 2022=654, 2023=651, 2024=881, 2025=840")
    print("  Nota EPA 2025: 110 excluidas sin num_expediente → ID sintético SIN_EXP_2025_XXX")
    print("  EELL: 2023=593, 2024=1137, 2025=1315")
    print("  Totales unificados esperados (tras dedup por tipo+expediente+anio):")
    print("    EPA=3351 (SUBV2022271 Peludosos dedup intra-año: se conserva la concedida;")
    print("              SUBV2022659 y 2023B628 reatribuidas a su convocatoria y deduplicadas), EELL=3045, Total=6396")
    print("  Periodos subvencionables: EPA 2021/2022/2025 y EELL 2024/2025 = anual (12m);")
    print("                           EPA 2023/2024 y EELL 2023 = semestral (6m)")
    print("  → Al comparar importes entre años tener en cuenta la diferencia de periodo.")

    print("======================================\n")


# =========================
# MAIN
# =========================

def main():

    archivos_epas = [
        ("data/processed/epas/2021/epas_2021.json", 2021),
        ("data/processed/epas/2022/epas_2022.json", 2022),
        ("data/processed/epas/2023/epas_2023.json", 2023),
        ("data/processed/epas/2024/epas_2024.json", 2024),
        ("data/processed/epas/2025/epas_2025.json", 2025),
    ]

    archivos_eell = [
        ("data/processed/eell/2023/resolucion-def-EELL2023.json", 2023),
        ("data/processed/eell/2024/resolucion-def-EELL2024.json", 2024),
        ("data/processed/eell/2025/eell_2025_completo.json",      2025),
    ]

    print("Cargando EPAs...")
    registros_epa = cargar_epas(archivos_epas)

    print("\nCargando EELL...")
    registros_eell = cargar_eell(archivos_eell)

    todos = registros_epa + registros_eell

    # Eliminar duplicados por (tipo, num_expediente, anio).
    # Incluir anio permite conservar el mismo número de expediente en años distintos
    # (ej: entidad que desistió en 2022 y consiguió la subvención en 2023).
    # Solo se colapsan duplicados dentro del mismo año (ej: SUBV2022271, Peludosos,
    # que aparece dos veces en el JSON 2022: una como concedida con importe y otra
    # como denegada sin importe, por estar en dos anexos distintos del BOE).
    # Regla de prioridad intra-año: se prefiere el registro con importe > 0
    # (concedida real) sobre cualquier otro. Si ambos tienen importe o ambos no
    # tienen, prevalece el último procesado.
    unique = {}
    for r in todos:
        key = (r["tipo"], r["num_expediente"], r["anio"])
        if key in unique:
            existente = unique[key]
            # Mantener el existente si tiene importe y el nuevo no
            if existente["importe"] > 0 and r["importe"] == 0.0:
                continue
        unique[key] = r

    final = list(unique.values())

    validar_y_mostrar(final)

    # Guardar
    os.makedirs("data/final", exist_ok=True)
    ruta_salida = "data/final/dataset_unificado.json"

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"Dataset guardado en: {ruta_salida}")
    print(f"Total registros: {len(final)}")


if __name__ == "__main__":
    main()
