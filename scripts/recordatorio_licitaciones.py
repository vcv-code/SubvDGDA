#!/usr/bin/env python3
"""
recordatorio_licitaciones.py — Aviso semestral para refrescar la tabla de
licitaciones de pienso para colonias.

POR QUÉ EXISTE. La web publica una tabla con los contratos públicos de pienso
para colonias que constan en la Plataforma de Contratación. Es un documento
útil justo porque está al día, y envejece solo: salen licitaciones todo el año
y nadie avisa. Un documento con fecha que nadie vuelve a tocar deja de ser una
prueba y pasa a ser una foto vieja.

POR QUÉ EN ENERO Y EN JULIO, y no cada seis meses contados desde hoy. Las
licitaciones no se reparten igual por el año: en los 64 contratos con fecha de
la primera tabla, marzo a junio concentra la mitad (32), y diciembre es el otro
pico (8), por el cierre de ejercicio. Enero y julio son los meses más flojos
(2 y 3). Así que el aviso cae justo DESPUÉS de cada oleada y en un mes tranquilo:
a mediados de enero el año anterior ya está cerrado, y a mediados de julio ya
ha pasado la temporada fuerte.

LA FECHA NO VA ESCRITA AQUÍ. Se lee de `frontend/recursos.html`, de la nota al
pie de la entrada de la tabla. Así el correo puede decir cuánto tiempo lleva sin
actualizarse sin que haya que tocar este script, y si alguien cambia la fecha en
la web al publicar una tabla nueva, el aviso se entera solo.

DÓNDE CORRE. En el HOST del servidor, por el `crontab` del sistema, como el
aviso de visitas y la copia de seguridad. Reutiliza su envío de correo.

Uso:
    python3 scripts/recordatorio_licitaciones.py          → manda el recordatorio
    python3 scripts/recordatorio_licitaciones.py --seco   → lo enseña, sin enviar
"""
import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RECURSOS = RAIZ / "frontend" / "recursos.html"
TABLA_PDF = "frontend/assets/docs/licitaciones-pienso-colonias-municipios.pdf"

BUSQUEDA = ("https://contrataciondelestado.es/wps/portal/licitaciones"
            "  (buscar: «colonias felinas», «gatos ferales», «gatos comunitarios»)")

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def _aviso_visitas():
    """Carga el script hermano para reutilizar su envío de correo."""
    spec = importlib.util.spec_from_file_location(
        "aviso_visitas", RAIZ / "scripts" / "aviso_visitas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fecha_publicada():
    """(mes, año) de los datos que hay hoy en la web, o None si no se encuentra.

    Se saca de la nota al pie de la entrada de la tabla en Recursos, con la
    forma «Datos a <mes> de <año>». Si alguien reescribe esa frase, el correo lo
    dice en vez de inventarse una fecha. El ejemplo va sin mes ni año concretos
    a propósito: escribirlos aquí sería duplicar el dato que se va a leer.
    """
    if not RECURSOS.exists():
        return None
    m = re.search(r"Datos a (\w+) de (\d{4})", RECURSOS.read_text(encoding="utf-8"))
    if not m:
        return None
    mes = m.group(1).lower()
    return (mes, int(m.group(2))) if mes in MESES else None


def _meses_desde(mes, anio, hoy):
    return (hoy.year - anio) * 12 + (hoy.month - MESES.index(mes) - 1)


def componer(hoy=None):
    hoy = hoy or date.today()
    pub = fecha_publicada()

    asunto = "Toca revisar la tabla de licitaciones de pienso"
    lineas = [
        "Recordatorio semestral: la tabla de licitaciones de pienso para",
        "colonias que publica la web conviene refrescarla.",
        "",
    ]

    if pub:
        mes, anio = pub
        meses = _meses_desde(mes, anio, hoy)
        lineas += [f"Los datos publicados son de {mes} de {anio}"
                   f" — hace {meses} meses." if meses else
                   f"Los datos publicados son de {mes} de {anio}.", ""]
    else:
        lineas += [
            "AVISO: no se ha podido leer la fecha de los datos en recursos.html.",
            "Puede que la nota al pie «Datos a <mes> de <año>» se haya reescrito.",
            "",
        ]

    lineas += [
        "Qué hacer:",
        "",
        "  1. Buscar en la Plataforma las licitaciones nuevas desde esa fecha:",
        f"     {BUSQUEDA}",
        "",
        "  2. Añadirlas a la hoja de cálculo y volver a exportarla a PDF.",
        "",
        f"  3. Sustituir {TABLA_PDF}",
        "     y actualizar la fecha de la nota al pie en frontend/recursos.html.",
        "",
        "  4. Revisar si cambian las cifras de la nota informativa: número de",
        "     contratos y de entidades, mediana por habitante y tabla por años.",
        "     Si cambian, hay que rehacer también ese PDF.",
        "",
        "Por qué ahora y no en otro momento: marzo-junio concentra la mitad de",
        "las licitaciones del año y diciembre es el otro pico, así que enero y",
        "julio caen justo después de cada oleada, cuando hay poco movimiento.",
    ]
    return asunto, "\n".join(lineas)


def main(argv):
    seco = "--seco" in argv
    av = _aviso_visitas()
    av.cargar_env()
    asunto, cuerpo = componer()
    if seco:
        print(f"Asunto: {asunto}\n")
        print(cuerpo)
        return 0
    return 0 if av.enviar(asunto, cuerpo, etiqueta="licitaciones") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
