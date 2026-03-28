import json
import pandas as pd
import os

JSON_PATH = "data/processed/eell/2025/BOE-A-2025-27204.json"
EXCEL_PATH = "data/raw/eell/2025/eell_2025.xlsx"
OUTPUT_PATH = "data/processed/eell/2025/eell_2025_completo.json"


def limpiar_importe(valor):
    if pd.isna(valor) or valor == "":
        return 0.0

    valor = str(valor).strip()
    valor = valor.replace("€", "").replace(" ", "")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", "")

    try:
        return float(valor)
    except:
        return 0.0


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.read_excel(EXCEL_PATH)

    # validar columnas
    df.columns = df.columns.str.strip().str.lower()

    if "num_expediente" not in df.columns or "importe" not in df.columns:
        raise ValueError("El Excel no tiene columnas 'num_expediente' e 'importe'")

    df["num_expediente"] = df["num_expediente"].astype(str).str.strip()

    importes = dict(zip(df["num_expediente"], df["importe"]))

    encontrados = 0

    for row in data:
        exp = str(row.get("num_expediente")).strip()

        if exp in importes:
            row["importe"] = limpiar_importe(importes[exp])
            encontrados += 1
        else:
            row["importe"] = 0.0

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON generado: {OUTPUT_PATH}")
    print(f"📊 Coincidencias encontradas: {encontrados} / {len(data)}")


if __name__ == "__main__":
    main()