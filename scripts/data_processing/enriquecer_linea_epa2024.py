"""
enriquecer_linea_epa2024.py
===========================
Añade el campo `linea` (línea de subvención) a data/processed/epas/2024/epas_2024.json,
cruzando por num_expediente con la relación de admitidas EPA 2024
(parser_EPAs_admitidas_2024). Así el dataset procesado de 2024 queda con el mismo
esquema que el de 2025, y unificar_datasets.py propaga la línea al dataset final.

Idempotente: re-ejecutarlo deja el mismo resultado. Los expedientes que no están
en el Anexo I de admitidas (o marcados "No aplica") quedan con linea=None.

Uso:
    python scripts/data_processing/enriquecer_linea_epa2024.py
    # luego regenerar el unificado:
    python scripts/data_processing/unificar_datasets.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_extractor"))
from parser_EPAs_admitidas_2024 import parsear_admitidas_epa2024  # noqa: E402

_PDF  = "data/raw/epas/2024/relacion-def-admitidas-EPA2024.pdf"
_JSON = "data/processed/epas/2024/epas_2024.json"


def main():
    mapa = {r["num_expediente"]: r["linea"] for r in parsear_admitidas_epa2024(_PDF)}

    with open(_JSON, encoding="utf-8") as f:
        registros = json.load(f)

    con_linea = 0
    for r in registros:
        # Añade `linea` como última clave (coincide con el esquema de 2025).
        r["linea"] = mapa.get(r["num_expediente"])
        if r["linea"]:
            con_linea += 1

    with open(_JSON, "w", encoding="utf-8") as f:
        f.write(json.dumps(registros, ensure_ascii=False, indent=2))

    print(f"epas_2024.json: {len(registros)} registros, {con_linea} con línea de subvención")


if __name__ == "__main__":
    main()
