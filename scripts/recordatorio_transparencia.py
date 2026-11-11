#!/usr/bin/env python3
"""
recordatorio_transparencia.py — Aviso para volver a preguntar qué ha pasado con
las subvenciones a entidades locales que no se justificaron.

POR QUÉ EXISTE. La página de EELL publica la respuesta de la Administración
sobre renuncias, pérdidas del derecho al cobro y reintegros. Esos datos tienen
una caducidad especialmente traicionera: los tres «ninguna» se leen como un
cierre y no lo son. Cuando se respondieron, la revisión de las cuentas
justificativas seguía abierta y de la convocatoria más reciente solo se había
contestado a parte de las preguntas.

Y es previsible que cambien. No justificar es causa de reintegro (Ley 38/2003,
art. 37.1.c), así que las entidades requeridas que no regularicen acabarán en
un expediente — justo el dato que hoy sale a cero. Si nadie vuelve a preguntar,
la web se queda diciendo «no se ha recuperado nada» cuando ya no sea verdad.

POR QUÉ UNA VEZ AL AÑO Y POR QUÉ EN MAYO. Se probó con dos avisos al año y no
sale bien: un expediente de este tipo dura más de seis meses en cuanto hay que
reclamar, así que el segundo recordatorio llega con el primero aún sin cerrar y
se solapan.

Mayo no es un mes cualquiera: es el que ya funcionó. La solicitud de 2026 entró
el 8 de mayo, la resolución llegó el 3 de julio, la reclamación se presentó el
17 de agosto y la respuesta buena el 9 de septiembre. Cuatro meses de principio
a fin, reclamación incluida, y todo dentro del mismo año natural. Empezando en
mayo cabe el ciclo completo —incluida la parte lenta— antes de que toque volver
a preguntar.

LA FECHA NO VA ESCRITA AQUÍ. Se lee de `frontend/estadisticas-eell.html`, de la
entradilla del bloque. Así, cuando se publiquen datos nuevos, el aviso se entera
solo y no hay que acordarse de tocar este fichero.

DÓNDE CORRE. En el HOST del servidor, por el `crontab` del sistema, como el
aviso de visitas y el de licitaciones. Reutiliza su envío de correo.

Uso:
    python3 scripts/recordatorio_transparencia.py          → manda el aviso
    python3 scripts/recordatorio_transparencia.py --seco   → lo enseña, sin enviar
"""
import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "frontend" / "estadisticas-eell.html"

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
    """(mes, año) de la respuesta publicada, o None si no se encuentra.

    Sale de la entradilla del bloque, con la forma «A <día> de <mes> de <año>
    respondió esto». Si alguien reescribe esa frase, el correo lo dice en vez
    de inventarse una fecha.
    """
    if not PAGINA.exists():
        return None
    texto = re.sub(r"<[^>]+>", "", PAGINA.read_text(encoding="utf-8"))
    m = re.search(r"A\s+\d{1,2}\s+de\s+(\w+)\s+de\s+(\d{4})\s+respondió", texto)
    if not m:
        return None
    mes = m.group(1).lower()
    return (mes, int(m.group(2))) if mes in MESES else None


def _meses_desde(mes, anio, hoy):
    return (hoy.year - anio) * 12 + (hoy.month - MESES.index(mes) - 1)


def componer(hoy=None):
    hoy = hoy or date.today()
    pub = fecha_publicada()

    asunto = "Toca volver a preguntar por las justificaciones de las EELL"
    lineas = [
        "Recordatorio: conviene pedir otra vez a la Dirección General de",
        "Derechos de los Animales el estado de las subvenciones a entidades",
        "locales que no se justificaron en plazo.",
        "",
    ]

    if pub:
        mes, anio = pub
        meses = _meses_desde(mes, anio, hoy)
        lineas += [
            f"Los datos publicados son de {mes} de {anio}"
            + (f" — hace {meses} meses." if meses else "."),
            "",
        ]
    else:
        lineas += [
            "AVISO: no se ha podido leer la fecha en estadisticas-eell.html.",
            "Puede que se haya reescrito la frase «A <día> de <mes> de <año>",
            "respondió esto» de la entradilla del bloque.",
            "",
        ]

    lineas += [
        "Qué preguntar (lo mismo que la vez anterior, por convocatoria):",
        "",
        "  · entidades que renuncian a la subvención",
        "  · entidades con pérdida total o parcial del derecho al cobro",
        "  · entidades con devolución voluntaria de fondos",
        "  · expedientes de reintegro iniciados o resueltos",
        "  · entidades que no han presentado la justificación",
        "  · estado de tramitación de los expedientes afectados",
        "",
        "Y pedir expresamente que, si alguna categoría aún no existe, lo",
        "declaren así en vez de denegar el acceso en bloque: eso es lo que",
        "desatascó la petición anterior.",
        "",
        "Qué revisar al recibir respuesta:",
        "",
        "  1. Actualizar las listas y la fecha en frontend/estadisticas-eell.html.",
        "  2. Ajustar los recuentos de los desplegables (dicen «5» y «21»).",
        "  3. Pasar tests/test_justificacion_eell.py, que vigila que la página",
        "     no llegue a decir que alguien devolvió dinero si no consta.",
        "",
        "OJO CON EL FONDO DEL ASUNTO. Que no conste ningún reintegro no",
        "significa que no vaya a haberlo: no justificar es causa de reintegro",
        "(Ley 38/2003, art. 37.1.c). Si las entidades requeridas no regularizan,",
        "ese dato dejará de ser cero — y es justo el que da sentido a todo esto,",
        "porque cada euro que no se aprovecha es uno que no llegó a las muchas",
        "entidades que se quedaron fuera por puntuación.",
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
    return 0 if av.enviar(asunto, cuerpo, etiqueta="transparencia") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
