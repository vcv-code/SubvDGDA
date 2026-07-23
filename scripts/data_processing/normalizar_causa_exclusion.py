"""
normalizar_causa_exclusion.py
=============================
Normaliza el campo `causa_exclusion` de data/final/dataset_unificado.json a un
formato canónico: uno o varios CÓDIGOS separados por ';' (p. ej. "2;6.a").

Motivo: cada anexo del BOE usa un separador distinto (';', ', ', '. ') y algunos
códigos llevan punto propio ('6.a', '3.1'). Además, EPA 2021 no usa códigos sino
el texto literal del motivo. Este paso deja todo homogéneo usando como fuente de
verdad el catálogo data/final/causas_exclusion.json:

  - EPA 2021 (texto literal)  → se mapea el texto a su código (1..6).
  - Resto (códigos)           → se tokeniza y se valida contra el catálogo.

Uso:
    python scripts/data_processing/normalizar_causa_exclusion.py [--dry-run]
"""
import json
import re
import sys

_DATASET = "data/final/dataset_unificado.json"
_CATALOGO = "data/final/causas_exclusion.json"


def _tokenizar(raw, codigos):
    """Tokeniza una cadena de códigos guiándose por el catálogo. '.' es a la vez
    separador ('2. 6.a', '16.18.19.') y parte de códigos ('3.1', '6.a'), así que
    se resuelve con match voraz del código válido más largo en cada posición.
    Los fragmentos que no casan con ningún código se devuelven tal cual (se
    reportarán como no resueltos)."""
    # Homogeneizar separadores: fuera espacios, ';'/',' pasan a '.'
    s = re.sub(r"\s+", "", raw)
    s = re.sub(r"[;,]", ".", s).strip(".")
    codes_desc = sorted(codigos, key=len, reverse=True)

    tokens, i = [], 0
    while i < len(s):
        elegido = None
        for c in codes_desc:
            if s[i:i + len(c)] == c and (i + len(c) == len(s) or s[i + len(c)] == "."):
                elegido = c
                break
        if elegido is None:
            nxt = s.find(".", i)
            elegido = s[i:] if nxt < 0 else s[i:nxt]
            i = len(s) if nxt < 0 else nxt + 1
        else:
            i += len(elegido)
            if i < len(s) and s[i] == ".":
                i += 1
        if elegido:
            tokens.append(elegido)
    return tokens


def normalizar(raw, codigos, texto_a_codigo):
    """Devuelve (causa_normalizada, tokens_no_resueltos)."""
    raw = str(raw).strip()
    if not raw:
        return None, []

    # Caso texto literal (EPA 2021): match exacto contra los motivos del catálogo.
    clave = raw.rstrip(".").strip().lower()
    if clave in texto_a_codigo:
        return texto_a_codigo[clave], []

    # Caso códigos: tokenizar (guiado por catálogo), dedup conservando orden.
    ordenados = []
    for t in _tokenizar(raw, codigos):
        if t not in ordenados:
            ordenados.append(t)
    no_resueltos = [t for t in ordenados if t not in codigos]
    return ";".join(ordenados), no_resueltos


def main():
    dry = "--dry-run" in sys.argv
    catalogo = json.load(open(_CATALOGO, encoding="utf-8"))
    registros = json.load(open(_DATASET, encoding="utf-8"))

    # índices por (tipo, anio)
    idx_codigos = {}
    idx_texto = {}
    for tipo, anios in catalogo.items():
        if tipo.startswith("_"):
            continue
        for anio, mapa in anios.items():
            idx_codigos[(tipo, anio)] = set(mapa.keys())
            idx_texto[(tipo, anio)] = {
                v["motivo"].rstrip(".").strip().lower(): k for k, v in mapa.items()
            }

    total = cambiados = 0
    problemas = []
    for r in registros:
        raw = r.get("causa_exclusion")
        if not raw:
            continue
        total += 1
        k = (r["tipo"], str(r["anio"]))
        codigos = idx_codigos.get(k, set())
        texto = idx_texto.get(k, {})
        nueva, no_res = normalizar(raw, codigos, texto)
        if no_res:
            problemas.append((r["tipo"], r["anio"], r.get("cif"), raw, no_res))
        if nueva != raw:
            cambiados += 1
            if not dry:
                r["causa_exclusion"] = nueva

    print(f"Registros con causa: {total} | normalizados: {cambiados}")
    if problemas:
        print(f"\n⚠ {len(problemas)} registros con tokens SIN resolver:")
        for p in problemas[:20]:
            print(f"   {p[0]} {p[1]} {p[2]}: {p[3]!r} -> no resuelto {p[4]}")
    else:
        print("✅ Todos los códigos resuelven contra el catálogo.")

    if not dry and not problemas:
        json.dump(registros, open(_DATASET, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\nGuardado {_DATASET}")
    elif not dry and problemas:
        print("\nNO se guarda: resuelve los problemas antes.")


if __name__ == "__main__":
    main()
