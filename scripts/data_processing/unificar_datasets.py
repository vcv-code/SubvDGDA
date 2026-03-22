import json
import os
from collections import Counter


def limpiar_importe(valor):
    if valor is None or valor == "":
        return 0.0
    try:
        return float(valor)
    except:
        return 0.0


def limpiar_cif(valor):
    """
    Limpia CIF:
    - None → None
    - "None" → None
    - "" → None
    - resto → string limpio
    """
    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "" or valor.lower() == "none":
        return None

    return valor


def limpiar_estado(valor):
    """
    Limpia estado:
    - None → None
    - "None" → None
    - "" → None
    - resto → minúsculas
    """
    if valor is None:
        return None

    valor = str(valor).strip().lower()

    if valor == "" or valor == "none":
        return None

    return valor


def procesar_json(ruta, anio):
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    registros = []

    for item in data:

        # validar expediente
        if not item.get("num_expediente"):
            continue

        registros.append({
            "anio": anio,
            "num_expediente": str(item.get("num_expediente")).strip(),
            "cif": limpiar_cif(item.get("cif")),
            "entidad": str(item.get("entidad")).strip(),
            "puntos": item.get("puntos"),
            "importe": limpiar_importe(item.get("importe")),
            "estado": limpiar_estado(item.get("estado")),
        })

    return registros


def main():
    resultado = []

    archivos_json = [
        ("data/processed/eell/2023/resolucion-def-EELL2023.json", 2023),
        ("data/processed/eell/2024/resolucion-def-EELL2024.json", 2024),
        ("data/processed/eell/2025/eell_2025_completo.json", 2025),
    ]

    for ruta, anio in archivos_json:
        if os.path.exists(ruta):
            resultado.extend(procesar_json(ruta, anio))
        else:
            print(f"⚠ No encontrado: {ruta}")

    # eliminar duplicados
    unique = {}
    for r in resultado:
        key = (r["anio"], r["num_expediente"])
        unique[key] = r

    final = list(unique.values())

    # 📊 validación por año
    conteo = Counter(r["anio"] for r in final)
    print("📊 Registros por año:", dict(conteo))

    # 📊 validación por estado
    conteo_estado = Counter(r["estado"] for r in final)
    print("📊 Registros por estado:", dict(conteo_estado))

    # ⚠ estados null
    estado_null = sum(1 for r in final if r["estado"] is None)
    print(f"⚠ Registros con estado null: {estado_null}")

    # ⚠ CIF null
    sin_cif = sum(1 for r in final if r["cif"] is None)
    print(f"⚠ Registros sin CIF: {sin_cif}")

    # 📊 estado solo 2025
    estado_2025 = [r["estado"] for r in final if r["anio"] == 2025]
    print("📊 Estado en 2025:", dict(Counter(estado_2025)))

    # guardar resultado
    os.makedirs("data/final", exist_ok=True)

    with open("data/final/dataset_unificado.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"✅ Registros finales: {len(final)}")


if __name__ == "__main__":
    main()