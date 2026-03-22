import pdfplumber
import re
import os


def limpiar_texto(valor):
    if not valor:
        return ""
    return str(valor).replace("\n", " ").strip()


def limpiar_importe(texto):
    if not texto:
        return 0.0

    texto = str(texto).strip()

    # eliminar símbolo €
    texto = texto.replace("€", "")

    # quitar espacios
    texto = texto.replace(" ", "")

    # si contiene coma → formato europeo
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")

    try:
        valor = float(texto)

        # filtro anti-valores rotos (muy importante)
        if valor < 100:  # ajustable si quieres
            return 0.0

        return valor
    except:
        return 0.0


def limpiar_puntos(texto):
    if not texto:
        return None
    try:
        return float(str(texto).replace(",", "."))
    except:
        return None


def parsear_eell_base(ruta_pdf):
    resultados = []

    with pdfplumber.open(ruta_pdf) as pdf:
        estado_actual = None

        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ""

            # Detectar anexo → estado
            if "ANEXO I" in texto:
                estado_actual = "concedida"
            elif "ANEXO II" in texto:
                estado_actual = "no_beneficiaria"
            elif "ANEXO III" in texto:
                estado_actual = "excluida"
            elif "ANEXO IV" in texto:
                estado_actual = "desistida"

            if estado_actual is None:
                continue

            tablas = pagina.extract_tables()

            for tabla in tablas:
                if not tabla or len(tabla) < 2:
                    continue

                for fila in tabla:
                    if not fila:
                        continue

                    fila = [limpiar_texto(c) for c in fila]

                    # validar expediente
                    expediente = fila[0]
                    if not re.match(r"EXP\d{4}", expediente):
                        continue

                    entidad = fila[1]
                    cif = fila[2]

                    puntos = None
                    importe = 0.0  # default

                    # --- CASO CONCEDIDA ---
                    if estado_actual == "concedida":

                        if len(fila) > 3:
                            puntos = limpiar_puntos(fila[3])

                        if len(fila) > 4:
                            importe = limpiar_importe(fila[4])

                    # --- NO BENEFICIARIA ---
                    elif estado_actual == "no_beneficiaria":

                        if len(fila) > 3:
                            puntos = limpiar_puntos(fila[3])

                    # otros estados → sin importe

                    resultado = {
                        "num_expediente": expediente,
                        "entidad": entidad,
                        "cif": cif,
                        "puntos": puntos,
                        "importe": importe,
                        "estado": estado_actual,
                        "_meta": {
                            "pagina": num_pagina,
                            "pdf": os.path.basename(ruta_pdf)
                        }
                    }

                    resultados.append(resultado)

    return resultados