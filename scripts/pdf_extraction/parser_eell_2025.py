from bs4 import BeautifulSoup
import json
import os


def parsear_eell_2025(ruta_xml):
    """
    Parser para BOE 2025 (usa HTML dentro del XML)
    """

    with open(ruta_xml, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    resultados = []
    vistos = set()

    filas = soup.find_all("tr")

    for fila in filas:
        celdas = fila.find_all("td")

        if len(celdas) < 3:
            continue

        expediente = celdas[0].get_text(strip=True)

        if not expediente.startswith("EXP2025"):
            continue

        if expediente in vistos:
            continue
        vistos.add(expediente)

        cif = celdas[1].get_text(strip=True)
        entidad = celdas[2].get_text(strip=True)

        puntos_texto = celdas[-1].get_text(strip=True)

        try:
            puntos = int(puntos_texto)
        except:
            puntos = None

        resultados.append({
            "num_expediente": expediente,
            "cif": cif,
            "entidad": entidad,
            "puntos": puntos,
            "estado": "concedida",
        })

    print(f"[BOE 2025] Registros únicos: {len(resultados)}")

    return resultados


def guardar_json(resultados, ruta_xml):
    nombre = os.path.basename(ruta_xml).replace(".xml", ".json")
    output = os.path.join("data/processed/eell/2025", nombre)

    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON guardado en: {output}")


if __name__ == "__main__":
    ruta = "data/raw/eell/2025/BOE-A-2025-27204.xml"

    resultados = parsear_eell_2025(ruta)
    guardar_json(resultados, ruta)