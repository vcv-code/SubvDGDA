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

Notas sobre el periodo subvencionable en EPAs:
  2021, 2022, 2025 → periodo anual   (12 meses)
  2023, 2024       → periodo semestral (6 meses)
  Tenerlo en cuenta al comparar importes entre años.

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

def cargar_epas(archivos):
    """
    Carga registros EPA desde sus JSON.
    Campos origen: anio, num_expediente, entidad, cif, puntuacion, importe, estado
    """
    registros = []
    contador_sin_exp = {}   # {anio: contador} para IDs sintéticos únicos

    for ruta, anio_fallback in archivos:
        if not os.path.exists(ruta):
            print(f"  AVISO: no encontrado → {ruta}")
            continue

        data = json.load(open(ruta, encoding="utf-8"))

        sin_exp_en_archivo = 0
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

            # El año del registro es siempre el año del fichero (convocatoria).
            # El campo 'anio' del JSON refleja el año codificado en el número de
            # expediente (ej: SUBV2022659 → 2022), que en registros cross-year
            # no coincide con el año de la convocatoria en que realmente participaron.
            # Usar anio_fallback garantiza que el mismo expediente en distintos
            # ficheros tenga años diferentes y no se duplique.
            anio_item = anio_fallback

            estado = normalizar_estado_epa(estado, anio_item)

            registros.append({
                "anio": anio_item,
                "tipo": "epa",
                "num_expediente": str(expediente_raw).strip(),
                "entidad": limpiar_entidad(item.get("entidad")),
                "cif": limpiar_cif(item.get("cif")),
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "linea": item.get("linea") or None,
                "tramo": None,           # las EPAs no tienen tramo
                "causa_exclusion": None, # las EPAs sí tienen causas de exclusión en el BOE,
                                         # pero no se capturan aún (mejora futura)
                "provincia": None,       # no derivable de CIF de asociación (mejora futura)
                "ccaa": None,            # idem
                "periodo_meses": 6 if anio_fallback in (2023, 2024) else 12,
                "es_agrupacion": False,
                "municipios_agrupacion": None,
            })

        aviso_sin_exp = f" ({sin_exp_en_archivo} sin expediente → ID sintético)" if sin_exp_en_archivo else ""
        print(f"  EPA {anio_fallback}: {len(data)} registros cargados desde {os.path.basename(ruta)}{aviso_sin_exp}")

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

            cif_limpio = limpiar_cif(item.get("cif"))
            provincia, ccaa = provincia_ccaa_de_cif(cif_limpio)

            registros.append({
                "anio": anio,
                "tipo": "eell",
                "num_expediente": str(item["num_expediente"]).strip(),
                "entidad": limpiar_entidad(item.get("entidad")),
                "cif": cif_limpio,
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "tramo": tramo,
                "causa_exclusion": causa,
                "provincia": provincia,
                "ccaa": ccaa,
                "periodo_meses": 12,     # las EELL siempre tienen periodo anual
                "es_agrupacion": bool(item.get("es_agrupacion", False)),
                "municipios_agrupacion": item.get("municipios_agrupacion"),
                # _meta se descarta intencionalmente
            })

        print(f"  EELL {anio}: {len(data)} registros cargados desde {os.path.basename(ruta)}")

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
    print("    EPA=3353 (SUBV2022271 Peludosos dedup intra-año: se conserva la concedida), EELL=3045, Total=6398")
    print("  Periodos subvencionables EPA: 2021/2022/2025=anual(12m), 2023/2024=semestral(6m)")
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
