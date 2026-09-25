#!/usr/bin/env python3
"""
historico_visitas.py — Acumula el histórico de visitas, mes a mes.

POR QUÉ EXISTE. Los registros de Nginx se borran a los 30 días
(`DIAS_RETENCION` en rotar_logs.py), así que el resumen de visitas solo puede
mirar ese último mes. Lo que no se guarde antes de esa fecha se pierde para
siempre: de julio de 2026 hacia atrás ya no queda nada.

CÓMO LO RESUELVE. Mantiene `informes/historico.json`, un fichero que solo crece:
una entrada por día con las visitas y las personas, y una entrada por periodo
con las páginas más vistas y las procedencias —esos dos vienen agregados en el
informe, no por día, así que se guardan tal cual con su rango de fechas—.

DE DÓNDE SACA LOS DATOS. De los propios informes HTML ya generados, que llevan
las cifras dentro. Eso permite dos cosas:

  · Sembrar el histórico con los informes viejos que hubiera guardados, que es
    como se recuperaron los 41 días de agosto y septiembre de 2026.
  · Alimentarlo solo: `traer_informes.sh` lo llama después de descargar, así que
    cada vez que se saca un informe el histórico se pone al día sin acordarse de
    nada. Aunque se pasen tres semanas sin mirarlo, el informe de 30 días
    rellena el hueco.

Uso:
    python3 scripts/historico_visitas.py                 → procesa informes/servidor/
    python3 scripts/historico_visitas.py fichero.html…   → procesa los que se indiquen
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent.parent

# Dónde se guarda. Configurable por una razón concreta y no por gusto:
# `informes/historico.json` está VERSIONADO —es el único fichero de esa carpeta
# que lo está—, y en el servidor lo escribe una tarea programada cada semana.
# Un fichero rastreado que se modifica solo en el servidor acaba abortando el
# `git pull` del siguiente despliegue con «local changes would be overwritten».
# Por eso allí se apunta a `historico-servidor.json`, que queda ignorado, y de
# ahí se lo trae `make informes` para fusionarlo con el versionado.
HISTORICO = Path(os.environ.get("HISTORICO_FILE",
                                str(RAIZ / "informes/historico.json")))

# Se miran las DOS carpetas, y no una, porque el mismo script corre en dos
# sitios con la estructura invertida:
#
#   · En el servidor, los informes los genera `resumen_visitas.py` en
#     `informes/` a secas. Ahí no existe `informes/servidor/`.
#   · En la máquina de trabajo, `informes/` guarda los informes LOCALES —el
#     trasteo con el Docker de desarrollo— y los del servidor se descargan a
#     `informes/servidor/`.
#
# Mezclar unos con otros falsearía el histórico, así que lo que separa el grano
# de la paja no es la carpeta sino `_es_local()`. Mirar las dos es seguro.
INFORMES = [RAIZ / "informes", RAIZ / "informes/servidor"]

# Las cifras van con punto de millar español: «3.166» son tres mil, no 3,166.
_NUM = re.compile(r"^[\d.]+$")


def _numero(txt):
    txt = txt.strip()
    return int(txt.replace(".", "")) if _NUM.match(txt) else None


def _limpiar(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def _periodo(html):
    """Rango que cubre el informe, del subtítulo: «2026-08-27 a 2026-09-25»."""
    m = re.search(r"(\d{4}-\d{2}-\d{2}) a (\d{4}-\d{2}-\d{2})", html)
    return (m.group(1), m.group(2)) if m else (None, None)


def _cifra(html, etiqueta):
    m = re.search(rf'cifra__num">([\d.]+)</div><div class="cifra__eti">{etiqueta}', html)
    return _numero(m.group(1)) if m else None


def _es_local(html):
    """Descarta los informes del Docker de desarrollo.

    Son el propio trasteo, no visitas: mezclarlos con los del servidor
    falsearía el histórico, y encima hacia arriba.

    Se miran dos señales, no una. La primera es la ruta del proyecto en el
    aviso de GeoIP: en local la base de MaxMind no está instalada y el informe
    dice dónde la busca, cosa que en el servidor no pasa. La segunda son las
    peticiones de robots, que en el servidor van por decenas de miles y en
    local apenas llegan a cien: cualquier web pública recibe muchísimo rastreo.

    Se combinan porque solas fallan. Bastaba con «menos de diez personas»
    —que era la versión anterior— para tirar un informe de UN día flojo de
    verdad del servidor; y la ruta desaparecería en cuanto se instalara GeoIP
    en local.
    """
    if "/home/ubuntu" in html or "\\home\\ubuntu" in html:
        return True
    personas = _cifra(html, "Personas distintas") or 0
    robots = _cifra(html, "Peticiones de robots") or 0
    return personas < 10 and robots < 1000


def _dias(html):
    """Visitas por día, del pie de cada barra de la gráfica."""
    return {d: int(n) for d, n in re.findall(r"(\d{4}-\d{2}-\d{2}): (\d+)", html)}


# Procedencias que no son tales y no deben guardarse.
#
# El histórico SÍ se versiona —es el único sitio donde viven los datos de más de
# 30 días, y perderlo sería perderlos— así que no puede llevar nada personal.
# Los agregados no lo son, pero por la cabecera Referer se cuelan dos cosas:
# direcciones IP desnudas, y cadenas de ataque como `${jndi:ldap:…}` de quien
# prueba a ver si el servidor es un Java vulnerable. Ni una ni otra son visitas.
_BASURA = re.compile(
    r"^\[?(?:\d{1,3}\.){3}\d{1,3}\]?$"      # IPv4, con o sin corchetes
    r"|^\[[0-9a-fA-F:]+\]$"                  # IPv6
    r"|[$}{]|jndi:|\$\{",                     # inyecciones en el Referer
    re.I)


def _procedencia_util(etiqueta):
    return not _BASURA.search(etiqueta)


def _tabla(html, titulo):
    """Filas (etiqueta, número) de la tabla que sigue a un encabezado dado."""
    m = re.search(rf"<h2[^>]*>{titulo}.*?</h2>(.*?)(?=<h2|</main|$)", html, re.S)
    if not m:
        return {}
    out = {}
    for a, b in re.findall(r"<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", m.group(1), re.S):
        n = _numero(_limpiar(b))
        if n is not None:
            out[_limpiar(a)] = n
    return out


def leer_informe(ruta):
    html = ruta.read_text(encoding="utf-8")
    if _es_local(html):
        return None
    desde, hasta = _periodo(html)
    return {
        "fichero": ruta.name,
        "desde": desde,
        "hasta": hasta,
        "dias": _dias(html),
        "paginas": _tabla(html, "Páginas más vistas"),
        "procedencias": {k: v for k, v in _tabla(html, "De dónde llegan").items()
                         if _procedencia_util(k)},
    }


def cargar():
    if HISTORICO.exists():
        return json.loads(HISTORICO.read_text(encoding="utf-8"))
    return {"dias": {}, "periodos": []}


def fusionar(hist, informe):
    """Incorpora un informe al histórico. Devuelve cuántos días son nuevos.

    Ante el mismo día visto en dos informes se conserva el valor MAYOR: un
    informe recién generado puede pillar un día a medias —el de hoy, sin
    terminar—, y el de la semana siguiente ya lo tiene completo.
    """
    nuevos = 0
    for d, n in informe["dias"].items():
        if d not in hist["dias"]:
            nuevos += 1
        hist["dias"][d] = max(hist["dias"].get(d, 0), n)

    # Los agregados van por periodo, no por día: no se pueden sumar sin mentir.
    clave = (informe["desde"], informe["hasta"])
    ya = {(p.get("desde"), p.get("hasta")) for p in hist["periodos"]}
    if clave not in ya and informe["desde"]:
        hist["periodos"].append({
            "desde": informe["desde"],
            "hasta": informe["hasta"],
            "paginas": informe["paginas"],
            "procedencias": informe["procedencias"],
        })
    return nuevos


def guardar(hist):
    hist["dias"] = dict(sorted(hist["dias"].items()))
    hist["periodos"].sort(key=lambda p: p.get("desde") or "")
    hist["actualizado"] = date.today().isoformat()
    HISTORICO.parent.mkdir(parents=True, exist_ok=True)
    HISTORICO.write_text(
        json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv):
    if argv[1:]:
        rutas = [Path(a) for a in argv[1:]]
    else:
        rutas = sorted(r for d in INFORMES if d.exists()
                       for r in d.glob("resumen-*.html"))
    if not rutas:
        sitios = " ni ".join(str(d) for d in INFORMES)
        print(f"No hay informes que procesar en {sitios}")
        return 1

    hist = cargar()
    antes = len(hist["dias"])
    saltados = 0
    for r in rutas:
        if not r.exists():
            print(f"  no existe: {r}")
            continue
        info = leer_informe(r)
        if info is None:
            saltados += 1
            continue
        n = fusionar(hist, info)
        if n:
            print(f"  {r.name}: {n} día(s) nuevo(s)")
    guardar(hist)

    ganados = len(hist["dias"]) - antes
    print(f"\nHistórico: {len(hist['dias'])} días"
          f" ({'+' + str(ganados) if ganados else 'sin cambios'})"
          f", {len(hist['periodos'])} periodo(s)")
    if saltados:
        print(f"Descartados {saltados} informe(s) locales: son trasteo propio, no visitas.")
    if hist["dias"]:
        print(f"Desde {min(hist['dias'])} hasta {max(hist['dias'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
