import re


def limpiar_texto(texto):
    if not texto:
        return ""

    # quitar saltos de línea
    texto = texto.replace("\n", " ")

    # quitar espacios duplicados
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def limpiar_cif(cif):
    if not cif:
        return None

    # coger solo el primero si hay varios
    return cif.split()[0]


def limpiar_puntos(valor):
    if not valor:
        return None

    valor = str(valor).lower()

    if "no aplica" in valor:
        return None

    if "recurso" in valor:
        return None

    # buscar número tipo 100,00 o 80
    import re
    match = re.search(r"\d+([.,]\d+)?", valor)

    if match:
        return float(match.group(0).replace(",", "."))

    return None