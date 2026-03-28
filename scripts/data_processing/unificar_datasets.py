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
    "estado":          str,          # concedida | denegada | excluida | desistida | no_beneficiaria
    "tramo":           int | None,  # 1, 2 o 3 solo para EELL 2025 concedidas; None en el resto
    "causa_exclusion": str | None   # código(s) de causa, solo en excluidas EELL; None en el resto
}

Notas sobre EELL 2023/2024 (PDF):
  El parser PDF devuelve todos los registros con estado='concedida'.
  Los que tienen importe=0 se reclasifican como 'no_beneficiaria'
  (superaron el baremo pero no recibieron fondos al quedar fuera del cupo).
  Los realmente excluidos (ANEXO III) no se capturan de forma fiable
  desde el PDF — para tenerlos habría que re-parsear o añadirlos manualmente.
"""

import json
import os
from collections import Counter


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
    v = str(valor).strip()
    if v == "" or v.lower() == "none":
        return None
    return v


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

            # Validar año: aceptar solo si es el año del archivo ±1
            # (el ±1 cubre el caso real del expediente 2023B628 en el fichero 2024).
            # Esto corrige el bug de EPAs 2022 donde el parser antiguo tomaba los
            # últimos 4 dígitos del número de expediente como año (ej: SUBV2022018 → 2018).
            anio_item = item.get("anio")
            if (not anio_item or not isinstance(anio_item, int)
                    or not (anio_fallback - 1 <= anio_item <= anio_fallback + 1)):
                anio_item = anio_fallback

            registros.append({
                "anio": anio_item,
                "tipo": "epa",
                "num_expediente": str(expediente_raw).strip(),
                "entidad": limpiar_entidad(item.get("entidad")),
                "cif": limpiar_cif(item.get("cif")),
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "tramo": None,           # las EPAs no tienen tramo
                "causa_exclusion": None, # las EPAs no tienen causa de exclusión
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

            registros.append({
                "anio": anio,
                "tipo": "eell",
                "num_expediente": str(item["num_expediente"]).strip(),
                "entidad": limpiar_entidad(item.get("entidad")),
                "cif": limpiar_cif(item.get("cif")),
                "puntuacion": puntuacion,
                "importe": importe,
                "estado": estado,
                "tramo": tramo,
                "causa_exclusion": causa,
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
    print(f"  Sin CIF:        {sin_cif}")
    print(f"  Sin entidad:    {sin_entidad}")
    print(f"  Importe = 0:    {sin_importe}")
    print(f"  Sin estado:     {sin_estado}")
    print(f"  Sin puntuación: {sin_puntuacion}")

    print("\nComparación con Excel de referencia:")
    print("  EPAs esperadas (aprox): 2021=328, 2022=654, 2023=651, 2024=882, 2025=841")
    print("  Nota EPA 2025: 110 excluidas sin num_expediente → ID sintético SIN_EXP_2025_XXX")
    print("  EELL esperadas (aprox): 2023=593, 2024=1137, 2025=1294")

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

    # Eliminar duplicados por (tipo, num_expediente)
    # En caso de duplicado, prevalece el último (más reciente)
    unique = {}
    for r in todos:
        key = (r["tipo"], r["num_expediente"])
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
