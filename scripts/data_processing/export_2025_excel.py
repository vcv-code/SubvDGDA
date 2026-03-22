import pandas as pd
import os

# rutas
INPUT = "data/processed/eell/2025/BOE-A-2025-27204.json"
OUTPUT = "data/raw/eell/2025/eell_2025.xlsx"

# cargar JSON
df = pd.read_json(INPUT)

# seleccionar solo columnas útiles
columnas = [
    "num_expediente",
    "entidad",
    "cif",
    "puntos"
]

df = df[columnas]

# ordenar
df = df.sort_values("num_expediente")

# añadir columna importe vacía
df["importe"] = ""

# guardar
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
df.to_excel(OUTPUT, index=False)

print(f"Excel generado: {OUTPUT} ({len(df)} filas)")