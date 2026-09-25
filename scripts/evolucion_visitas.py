#!/usr/bin/env python3
"""
evolucion_visitas.py — Informe de evolución mes a mes.

POR QUÉ VA APARTE DEL RESUMEN. El resumen de visitas contesta «cómo va este
mes». Esta contesta otra pregunta: «va a mejor o a peor». Son lecturas
distintas y mezclarlas en un solo fichero acaba en una página que nadie lee
entera.

DE DÓNDE SALEN LOS DATOS. De `informes/historico.json`, que mantiene
`historico_visitas.py` a partir de los informes ya generados. No mira los
registros de Nginx: esos solo llegan a 30 días atrás, que es precisamente el
motivo de que exista el histórico.

HONESTIDAD CON LOS MESES INCOMPLETOS. Un mes del que solo hay 17 días no se
puede comparar con uno de 30 sin mentir. Se marcan como incompletos, se indica
cuántos días tienen y se da también la media diaria, que sí es comparable.

Uso:
    python3 scripts/evolucion_visitas.py            → genera y abre en el navegador
    ABRIR=no python3 scripts/evolucion_visitas.py   → solo genera
"""
import calendar
import html
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).parent.parent
HISTORICO = RAIZ / "informes/historico.json"
DESTINO = RAIZ / "informes"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CSS = """
:root { --verde:#2E7D32; --gris:#6B7280; --borde:#E5E7EB; --fondo:#F9FAFB;
        --ambar:#D97706; }
* { box-sizing:border-box; }
body { margin:0; padding:2rem 1rem; background:var(--fondo);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif; color:#111827;
       line-height:1.6; }
.envoltorio { max-width:900px; margin:0 auto; }
h1 { font-size:1.5rem; margin:0 0 .25rem; }
.periodo { color:var(--gris); font-size:.9rem; margin:0 0 2rem; }
h2 { font-size:1.1rem; margin:2.5rem 0 .75rem; padding-bottom:.4rem;
     border-bottom:2px solid var(--verde); }
h2 .pista { font-weight:400; font-size:.85rem; color:var(--gris);
            display:block; border:0; margin-top:.2rem; }
table { width:100%; border-collapse:collapse; background:#fff;
        border:1px solid var(--borde); border-radius:8px; overflow:hidden; }
th,td { padding:.6rem .8rem; text-align:left; border-bottom:1px solid var(--borde);
        font-size:.95rem; }
th { color:var(--gris); font-weight:600; font-size:.85rem; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
tr:last-child td { border-bottom:0; }
.grafica { background:#fff; border:1px solid var(--borde); border-radius:8px;
           padding:1rem; }
.grafica svg { width:100%; height:auto; display:block; }
.aviso { background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px;
         padding:1rem; font-size:.9rem; margin-top:1rem; }
.sube { color:var(--verde); font-weight:600; }
.baja { color:#C62828; font-weight:600; }
.parcial { color:var(--ambar); font-size:.8rem; }
.imprimir { float:right; background:var(--verde); color:#fff; border:0;
            border-radius:6px; padding:.5rem .9rem; cursor:pointer;
            font-family:inherit; }
/* Los navegadores no imprimen fondos por defecto: sin esto, las tarjetas y el
   aviso salen en blanco al guardar como PDF. La gráfica no lo necesita porque
   va en SVG, que sí se imprime. */
@media print {
    .imprimir { display:none; }
    body { background:#fff; padding:0; }
    table, .aviso { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    h2 { break-after:avoid; }
    table { break-inside:avoid; }
}
"""


def fmt(n):
    return f"{n:,}".replace(",", ".")


def cargar():
    if not HISTORICO.exists():
        raise SystemExit(
            f"ERROR: no existe {HISTORICO}.\n"
            "Ejecuta antes: python3 scripts/historico_visitas.py")
    return json.loads(HISTORICO.read_text(encoding="utf-8"))


def por_meses(dias):
    """Agrupa por mes y marca los incompletos.

    Completo significa tener dato de TODOS los días del mes. El mes en curso
    nunca lo está, y los que se recuperaron a medias de informes viejos
    tampoco: en los dos casos la cifra total engaña y la media diaria no.
    """
    acum = defaultdict(int)
    cuenta = defaultdict(int)
    for d, n in dias.items():
        acum[d[:7]] += n
        cuenta[d[:7]] += 1

    hoy = date.today()
    out = []
    for mes in sorted(acum):
        anio, num = int(mes[:4]), int(mes[5:7])
        del_mes = calendar.monthrange(anio, num)[1]
        # Del mes en curso solo han transcurrido los días hasta hoy.
        esperados = hoy.day if (anio, num) == (hoy.year, hoy.month) else del_mes
        en_curso = (anio, num) == (hoy.year, hoy.month)
        out.append({
            "mes": mes,
            "nombre": f"{MESES[num - 1]} {anio}",
            "total": acum[mes],
            "dias": cuenta[mes],
            "esperados": esperados,
            # Del mes: cuántos días tiene en total, para decir «25 de 30».
            "del_mes": del_mes,
            "en_curso": en_curso,
            # Completo = no le falta ningún día de los que ya han pasado. El mes
            # en curso puede estar completo en ese sentido y aun así no ser
            # comparable por TOTAL con uno entero, de ahí las dos banderas.
            "completo": cuenta[mes] >= esperados,
            "media": round(acum[mes] / cuenta[mes], 1),
        })
    return out


def grafica(meses, ancho=860, alto=240):
    """Gráfica de barras en SVG, sin librerías ni conexión.

    En SVG y no con `div` de fondo CSS por un motivo concreto: los navegadores
    NO imprimen fondos de color por defecto, así que unas barras hechas con
    `background` salen en blanco al guardar como PDF. El `fill` de un SVG sí se
    imprime. Es el mismo enfoque que usa resumen_visitas.py, que por eso
    imprimía bien.

    La escala va por MEDIA DIARIA y no por total: con meses incompletos la
    altura por total haría parecer que agosto fue peor cuando solo tiene menos
    días medidos.
    """
    if not meses:
        return "<p>Todavía no hay datos.</p>"
    tope = max(m["media"] for m in meses) or 1
    margen, base = 44, alto - 46
    paso = (ancho - margen - 10) / len(meses)
    ancho_barra = max(6, min(paso * 0.55, 90))

    p = [f'<svg viewBox="0 0 {ancho} {alto}" role="img" '
         f'aria-label="Media de visitas al día, por mes">',
         '<defs><pattern id="rayas" width="10" height="10" '
         'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="10" height="10" fill="#2E7D32"/>'
         '<rect width="5" height="10" fill="#A5D6A7"/></pattern></defs>',
         f'<line x1="{margen}" y1="{base}" x2="{ancho-10}" y2="{base}" stroke="#E5E7EB"/>',
         f'<text x="4" y="16" font-size="11" fill="#6B7280">{tope:g}</text>']

    for i, m in enumerate(meses):
        h = max(2, (m["media"] / tope) * (base - 34))
        x = margen + i * paso + (paso - ancho_barra) / 2
        # Rayado tanto si faltan días medidos como si el mes sigue corriendo:
        # en los dos casos el total engaña, aunque la media no.
        relleno = "#2E7D32" if (m["completo"] and not m["en_curso"]) else "url(#rayas)"
        titulo = (f'{m["nombre"]}: {fmt(m["total"])} visitas en '
                  f'{m["dias"]} día(s), media {m["media"]:g}')
        p.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{ancho_barra:.1f}" '
                 f'height="{h:.1f}" fill="{relleno}" rx="3">'
                 f'<title>{html.escape(titulo)}</title></rect>')
        p.append(f'<text x="{x+ancho_barra/2:.1f}" y="{base-h-7:.1f}" font-size="12" '
                 f'font-weight="600" fill="#111827" text-anchor="middle">'
                 f'{m["media"]:g}</text>')
        p.append(f'<text x="{x+ancho_barra/2:.1f}" y="{base+16:.1f}" font-size="11" '
                 f'fill="#6B7280" text-anchor="middle">{m["nombre"].split()[0][:3]}</text>')
        p.append(f'<text x="{x+ancho_barra/2:.1f}" y="{base+30:.1f}" font-size="10" '
                 f'fill="#9CA3AF" text-anchor="middle">{m["mes"][:4]}</text>')
    p.append("</svg>")
    return '<div class="grafica">' + "".join(p) + "</div>"


def tabla_meses(meses):
    filas = []
    previo = None
    for m in meses:
        if previo is None:
            var = "—"
        else:
            # Se compara la media diaria, que es lo único comparable entre un
            # mes entero y otro a medias.
            d = (m["media"] - previo["media"]) / previo["media"] * 100 if previo["media"] else 0
            clase = "sube" if d >= 0 else "baja"
            var = f'<span class="{clase}">{d:+.0f} %</span>'
        if m["en_curso"]:
            marca = (f' <span class="parcial">· en curso, {m["dias"]} de '
                     f'{m["del_mes"]} días</span>')
        elif not m["completo"]:
            marca = (f' <span class="parcial">· {m["dias"]} de '
                     f'{m["del_mes"]} días</span>')
        else:
            marca = ""
        filas.append(
            f'<tr><td>{html.escape(m["nombre"])}{marca}</td>'
            f'<td class="num">{fmt(m["total"])}</td>'
            f'<td class="num">{m["media"]:g}</td>'
            f'<td class="num">{var}</td></tr>')
        previo = m
    return ('<table><tr><th>Mes</th><th style="text-align:right">Visitas</th>'
            '<th style="text-align:right">Media diaria</th>'
            '<th style="text-align:right">Variación</th></tr>'
            + "".join(filas) + "</table>")


def tabla_periodos(periodos, clave, titulo, pista):
    """Páginas o procedencias, un periodo por columna.

    No se suman entre periodos porque se solapan: dos informes de 30 días
    sacados con una semana de diferencia comparten 23 días, y sumarlos
    contaría esos días dos veces.
    """
    utiles = [p for p in periodos if p.get(clave)]
    if not utiles:
        return ""
    # Por fecha de CIERRE, que es lo que etiqueta cada columna. Ordenar por
    # fecha de inicio deja un informe de 30 días delante de otro de 7 que es
    # posterior, y la tabla se lee al revés de como va el tiempo.
    utiles = sorted(utiles, key=lambda p: p.get("hasta") or "")[-4:]
    etiquetas = set()
    for p in utiles:
        etiquetas.update(p[clave])
    orden = sorted(etiquetas, key=lambda e: -sum(p[clave].get(e, 0) for p in utiles))[:12]

    cab = "".join(f'<th style="text-align:right">{html.escape(p["hasta"][5:])}</th>'
                  for p in utiles)
    filas = []
    for e in orden:
        celdas = "".join(
            f'<td class="num">{fmt(p[clave][e]) if e in p[clave] else "—"}</td>'
            for p in utiles)
        filas.append(f"<tr><td>{html.escape(e)}</td>{celdas}</tr>")
    return (f'<h2>{titulo}<span class="pista">{pista}</span></h2>'
            f"<table><tr><th>{'Página' if clave == 'paginas' else 'Procedencia'}</th>"
            f"{cab}</tr>" + "".join(filas) + "</table>")


def main():
    hist = cargar()
    dias = hist.get("dias", {})
    if not dias:
        raise SystemExit("El histórico está vacío.")
    meses = por_meses(dias)
    periodos = hist.get("periodos", [])

    incompletos = [m["nombre"] for m in meses if not m["completo"] or m["en_curso"]]
    aviso = ""
    if incompletos:
        aviso = (
            '<div class="aviso"><strong>Meses con datos parciales:</strong> '
            + ", ".join(html.escape(m) for m in incompletos)
            + ". Se marcan con la barra rayada. Los registros de Nginx se borran "
              "a los 30 días, así que de los meses anteriores solo se conserva lo "
              "que quedó recogido en algún informe. <strong>Compara la media "
              "diaria, no el total.</strong></div>")

    ahora = datetime.now()
    cuerpo = [
        '<button class="imprimir" onclick="window.print()">Guardar como PDF</button>',
        "<h1>Evolución de las visitas</h1>",
        f'<p class="periodo">subvencionesdgda.org · {min(dias)} a {max(dias)} · '
        f'generado el {ahora:%d/%m/%Y a las %H:%M}</p>',
        '<h2>Media de visitas al día, por mes'
        '<span class="pista">La altura va por media diaria y no por total, '
        'para que un mes a medias no parezca peor de lo que fue.</span></h2>',
        grafica(meses),
        '<h2>Mes a mes<span class="pista">La variación compara la media diaria '
        'con la del mes anterior.</span></h2>',
        tabla_meses(meses),
        aviso,
        tabla_periodos(periodos, "paginas", "Páginas más vistas",
                       "Una columna por informe guardado, con su fecha de cierre. "
                       "No se suman: los periodos se solapan."),
        tabla_periodos(periodos, "procedencias", "De dónde llegan",
                       "Mismo criterio: cada columna es un informe, no un total."),
    ]

    salida = DESTINO / f"evolucion-{date.today().isoformat()}.html"
    salida.write_text(
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>Evolución de visitas — subvencionesdgda.org</title>"
        f"<style>{CSS}</style></head><body><div class=\"envoltorio\">"
        + "".join(c for c in cuerpo if c)
        + "</div></body></html>", encoding="utf-8")
    print(f"Listo: {salida}")
    print(f"{len(meses)} mes(es), {len(dias)} días de datos.")
    print("El botón «Guardar como PDF» de arriba abre el diálogo de impresión.")

    if os.environ.get("ABRIR", "si") == "si":
        abrir(salida)
    return 0


# Rutas habituales de Chrome en Windows. Se prefiere a abrir con el navegador
# predeterminado porque en esta máquina es Edge, y el informe se revisa en
# Chrome. Con NAVEGADOR se puede forzar otro o volver al predeterminado.
CHROME = [
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
    "/mnt/c/Users/%s/AppData/Local/Google/Chrome/Application/chrome.exe",
]


def _chrome():
    """Ruta a Chrome, o None si no está."""
    elegido = os.environ.get("NAVEGADOR", "").strip()
    if elegido and elegido != "chrome":
        # Puede ser «predeterminado» o la ruta de otro navegador.
        return None if elegido == "predeterminado" else elegido
    for c in CHROME:
        if "%s" in c:
            continue
        if Path(c).exists():
            return c
    return None


def abrir(ruta):
    """Abre el informe en el navegador.

    En WSL hay que traducir la ruta al formato de Windows: el navegador es una
    aplicación de Windows y no entiende las rutas de Linux.

    Se prefiere Chrome porque es donde se revisan los informes; si no está, se
    cae al navegador predeterminado. `NAVEGADOR=predeterminado` fuerza ese
    camino, y `NAVEGADOR=/ruta/al/navegador.exe` usa otro.
    """
    if not shutil.which("wslpath"):
        if shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(ruta)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f"Ábrelo a mano: {ruta}")
        return

    win = subprocess.run(["wslpath", "-w", str(ruta)],
                         capture_output=True, text=True).stdout.strip()
    navegador = _chrome()
    if navegador:
        subprocess.Popen([navegador, win],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Abriendo en {Path(navegador).stem}...")
    elif shutil.which("explorer.exe"):
        # explorer.exe devuelve código 1 aunque abra bien, así que se ignora.
        subprocess.run(["explorer.exe", win], capture_output=True)
        print("Abriendo en el navegador predeterminado...")
    else:
        print(f"Ábrelo a mano: {ruta}")


if __name__ == "__main__":
    sys.exit(main())
