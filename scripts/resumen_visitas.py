#!/usr/bin/env python3
"""
resumen_visitas.py — Resumen legible de las visitas, en español.

Complementa a informe_visitas.sh (GoAccess), que da el detalle completo pero
en inglés y con más paneles de los que hacen falta a diario. Esto responde a
cinco preguntas y se acaba:

    ¿Cuánta gente entra? · ¿Qué miran? · ¿De dónde llegan?
    ¿Con qué dispositivo? · ¿Qué está fallando?

Sin dependencias: solo biblioteca estándar. La gráfica es un SVG generado
aquí mismo, así que el HTML se abre en cualquier navegador sin conexión.

Qué se descuenta y por qué
──────────────────────────
· Rastreadores y sondeos: en una web pública son la mayor parte del tráfico.
  Contarlos como visitas daría cifras infladas y sin sentido.
· Ficheros estáticos (imágenes, CSS, JS): una sola visita a una página pide
  veinte ficheros. Lo que interesa es la página, no sus piezas.

Uso:
    python3 scripts/resumen_visitas.py
    python3 scripts/resumen_visitas.py --dias 7
"""
import argparse
import html
import os
import re
import socket
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

RAIZ    = Path(__file__).parent.parent
LOG_DIR = RAIZ / "logs/nginx"
DESTINO = RAIZ / "informes"

# Mismo formato que log_format bdns en docker/nginx/default.conf
LINEA = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<fecha>[^:]+):(?P<hora>\d{2}):\d{2}:\d{2}[^\]]*\] '
    r'"(?P<metodo>\S+) (?P<ruta>\S+) [^"]*" (?P<estado>\d{3}) \S+ '
    r'"(?P<referente>[^"]*)" "(?P<agente>[^"]*)"'
)

BOTS = re.compile(
    r'bot|crawler|spider|slurp|scrap|curl|wget|python-requests|go-http|'
    r'headless|monitor|scan|nmap|masscan|zgrab|facebookexternal|preview',
    re.I,
)
ESTATICOS = re.compile(r'\.(css|js|png|jpe?g|webp|svg|ico|woff2?|ttf|map|json|txt)$', re.I)
MOVIL     = re.compile(r'Mobile|Android|iPhone|iPod', re.I)
TABLETA   = re.compile(r'iPad|Tablet', re.I)

MESES = {m: i for i, m in enumerate(
    ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}


ROBOTS_CONOCIDOS = [
    ('Googlebot',        'Google (indexa la web)'),
    ('bingbot',          'Bing (indexa la web)'),
    ('DuckDuckBot',      'DuckDuckGo'),
    ('YandexBot',        'Yandex'),
    ('Applebot',         'Apple'),
    ('facebookexternal', 'Facebook (previsualización de enlaces)'),
    ('Twitterbot',       'X/Twitter (previsualización)'),
    ('WhatsApp',         'WhatsApp (previsualización)'),
    ('AhrefsBot',        'Ahrefs (SEO comercial)'),
    ('SemrushBot',       'Semrush (SEO comercial)'),
    ('MJ12bot',          'Majestic (SEO comercial)'),
    ('PetalBot',         'Huawei'),
    ('GPTBot',           'OpenAI (entrenamiento de IA)'),
    ('CCBot',            'Common Crawl (archivo público)'),
    ('ClaudeBot',        'Anthropic (entrenamiento de IA)'),
    ('curl',             'curl (pruebas o scripts)'),
    ('python-requests',  'script en Python'),
    ('zgrab',            'escaneo automático'),
    ('masscan',          'escaneo automático'),
    ('nmap',             'escaneo automático'),
]


def nombre_robot(agente):
    for clave, nombre in ROBOTS_CONOCIDOS:
        if clave.lower() in agente.lower():
            return nombre
    return 'Otros robots y escaneos'


# ── Identificación de organizaciones ────────────────────────────────────────
# Se resuelve el nombre de la máquina (DNS inverso) de las IPs que más páginas
# han visto, y se busca si pertenece a una administración pública.
#
# Esto identifica ORGANIZACIONES, no personas: que un ayuntamiento consulte
# datos sobre sus propias subvenciones es información legítima y de interés
# público. Nunca se muestra la IP, solo el organismo.
#
# Va desactivado por defecto (--organizaciones) porque cada consulta es una
# petición de red: con cientos de IPs, tarda.
ORGANISMOS = [
    (r'\.gob\.es$',                     'Administración General del Estado'),
    (r'ayto|ayuntamiento',              'Ayuntamiento'),
    (r'dipu|diputacio',                 'Diputación provincial'),
    (r'\.gencat\.cat$',                 'Generalitat de Catalunya'),
    (r'juntadeandalucia',               'Junta de Andalucía'),
    (r'\.xunta\.(es|gal)$',             'Xunta de Galicia'),
    (r'euskadi|ejgv',                   'Gobierno Vasco'),
    (r'\.navarra\.es$',                 'Gobierno de Navarra'),
    (r'\.gva\.es$',                     'Generalitat Valenciana'),
    (r'\.jcyl\.es$',                    'Junta de Castilla y León'),
    (r'\.jccm\.es$',                    'Castilla-La Mancha'),
    (r'\.madrid\.org$|\.comunidad\.madrid$', 'Comunidad de Madrid'),
    (r'\.aragon\.es$',                  'Gobierno de Aragón'),
    (r'\.larioja\.org$',                'Gobierno de La Rioja'),
    (r'\.carm\.es$',                    'Región de Murcia'),
    (r'\.juntaex\.es$',                 'Junta de Extremadura'),
    (r'\.princast\.es$',                'Principado de Asturias'),
    (r'\.cantabria\.es$',               'Gobierno de Cantabria'),
    (r'\.caib\.es$',                    'Govern de les Illes Balears'),
    (r'\.gobiernodecanarias\.',         'Gobierno de Canarias'),
    (r'rediris|\.uned\.es$|\.csic\.es$', 'Universidad o investigación pública'),
    (r'\.congreso\.es$|\.senado\.es$',  'Cortes Generales'),
    (r'\.guardiacivil\.|\.policia\.',   'Fuerzas y cuerpos de seguridad'),
]


def organizacion(ip, cache):
    """Nombre del organismo si la IP resuelve a una administración pública."""
    if ip in cache:
        return cache[ip]
    try:
        nombre = socket.gethostbyaddr(ip)[0].lower()
    except (OSError, socket.herror, socket.gaierror):
        cache[ip] = None
        return None
    for patron, etiqueta in ORGANISMOS:
        if re.search(patron, nombre):
            cache[ip] = etiqueta
            return etiqueta
    cache[ip] = None
    return None


# ── Geolocalización (opcional) ──────────────────────────────────────────────
# País y ciudad a partir de la IP, con la base GeoLite2 de MaxMind.
#
# Es OPCIONAL a propósito: si falta la librería o la base, el resumen se
# genera igual sin esa sección. Así se mantiene la promesa de que el script
# funciona en un servidor pelado, sin instalar nada.
#
# Para activarlo:
#   pip install maxminddb
#   y dejar GeoLite2-City.mmdb en datos/geoip/ (o apuntar con GEOIP_DB)
GEOIP_DB = Path(os.environ.get(
    "GEOIP_DB", RAIZ / "datos/geoip/GeoLite2-City.mmdb"))
GEOIP_ASN = Path(os.environ.get(
    "GEOIP_ASN", RAIZ / "datos/geoip/GeoLite2-ASN.mmdb"))

# Redes de alojamiento y nube. El tráfico que sale de aquí NO es gente leyendo
# la web: son rastreadores y escáneres alojados en servidores que, a diferencia
# de Googlebot, no se identifican como robots en su agente de usuario.
#
# Se detectó al ver el informe: entre las ciudades con más "visitas" salían
# Ashburn, Boardman, Santa Clara y Phoenix, que no son sitios donde vive gente
# sino donde están los centros de datos de Amazon, Google y Microsoft. Sin
# filtrarlas, Estados Unidos encabezaba la lista con casi el triple que España.
#
# MaxMind no marca "esto es alojamiento" en la base gratuita, así que se
# reconoce por el nombre de la red. No es exhaustivo —salen proveedores nuevos
# constantemente— pero cubre a los grandes, que son la mayor parte.
REDES_NUBE = re.compile(
    # Nubes y proveedores de alojamiento
    r'amazon|aws|google|microsoft|azure|digitalocean|digital ocean|linode|'
    r'akamai|fastly|cloudflare|oracle|alibaba|tencent|huawei|ovh|hetzner|'
    r'contabo|scaleway|leaseweb|vultr|choopa|m247|datacamp|hostinger|godaddy|'
    r'namecheap|ionos|1&1|aruba|netcup|upcloud|kamatera|quadranet|psychz|'
    r'hostwinds|stackpath|bunny|cdn77|equinix|digitalrealty|'
    # Grandes tecnológicas: sus rangos son centros de datos, no domicilios.
    # El tráfico doméstico de sus usuarios sale por la operadora, no por aquí.
    r'meta platforms|facebook|linkedin|twitter|x corp|apple inc|bytedance|'
    r'yandex|baidu|openai|anthropic|perplexity|'
    # Genéricos que aparecen en muchos nombres de red
    r'data ?cent(er|re)|hosting|server|cloud|vps|colo',
    re.I,
)


def abrir_asn():
    """Lector de GeoLite2-ASN, o None. Opcional como el de ciudades."""
    try:
        import maxminddb
    except ImportError:
        return None
    if not GEOIP_ASN.exists():
        return None
    try:
        return maxminddb.open_database(str(GEOIP_ASN))
    except Exception:
        return None


def red_de(lector, ip):
    """Nombre de la red (operador) a la que pertenece la IP, o None."""
    if not lector:
        return None
    try:
        d = lector.get(ip)
    except (ValueError, TypeError):
        return None
    return (d or {}).get('autonomous_system_organization')


def abrir_geoip():
    """Devuelve el lector de GeoLite2, o None si no se puede usar."""
    try:
        import maxminddb
    except ImportError:
        return None, "falta la librería: pip install maxminddb"
    if not GEOIP_DB.exists():
        return None, f"falta la base de datos en {GEOIP_DB}"
    try:
        return maxminddb.open_database(str(GEOIP_DB)), None
    except Exception as e:
        return None, f"no se pudo abrir la base: {e}"


def ubicacion(lector, ip):
    """(país, ciudad) o (None, None). La ciudad suele fallar en móviles."""
    try:
        d = lector.get(ip)
    except (ValueError, TypeError):
        return None, None
    if not d:
        return None, None
    pais = (d.get('country') or d.get('registered_country') or {})
    pais = (pais.get('names') or {}).get('es') or (pais.get('names') or {}).get('en')
    ciudad = ((d.get('city') or {}).get('names') or {}).get('es') \
        or ((d.get('city') or {}).get('names') or {}).get('en')
    return pais, ciudad


def navegador(agente):
    for clave, nombre in [('Edg', 'Edge'), ('OPR', 'Opera'), ('Firefox', 'Firefox'),
                          ('Chrome', 'Chrome'), ('Safari', 'Safari')]:
        if clave in agente:
            return nombre
    return 'Otro'


def dispositivo(agente):
    if TABLETA.search(agente):
        return 'Tableta'
    return 'Móvil' if MOVIL.search(agente) else 'Escritorio'


def leer(dias):
    """Devuelve las peticiones de personas, sin bots ni ficheros estáticos."""
    corte = datetime.now() - timedelta(days=dias)
    filas, descartadas = [], Counter()

    for f in sorted(LOG_DIR.glob("access.log*")):
        for linea in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LINEA.match(linea)
            if not m:
                descartadas['formato'] += 1
                continue
            d = m.groupdict()
            try:
                dia, mes, anio = d['fecha'].split('/')
                fecha = datetime(int(anio), MESES[mes], int(dia))
            except (ValueError, KeyError):
                descartadas['fecha'] += 1
                continue
            if fecha < corte:
                continue
            if BOTS.search(d['agente']):
                descartadas['bots'] += 1
                d['es_bot'] = True
                d['fecha_obj'] = fecha
                filas.append(d)
                continue
            d['fecha_obj'] = fecha
            filas.append(d)
    return filas, descartadas


def construir(filas, descartadas, dias, resolver_dns=False):
    paginas   = Counter()
    api       = Counter()
    por_dia   = defaultdict(set)
    hits_dia  = Counter()
    referentes = Counter()
    dispositivos = Counter()
    navegadores  = Counter()
    fallos    = Counter()
    horas     = Counter()
    visitantes = set()

    robots = Counter()
    hits_ip = Counter()
    nube = Counter()          # peticiones desde redes de alojamiento
    lector_asn = abrir_asn()
    cache_nube = {}

    def desde_centro_de_datos(ip):
        if ip not in cache_nube:
            red = red_de(lector_asn, ip)
            cache_nube[ip] = (red, bool(red and REDES_NUBE.search(red)))
        return cache_nube[ip]

    for d in filas:
        if d.get('es_bot'):
            robots[nombre_robot(d['agente'])] += 1
            continue
        ruta, estado, ip = d['ruta'].split('?')[0], d['estado'], d['ip']

        # Tráfico de centros de datos: se descuenta como los robots, porque es
        # lo mismo sin declararse. Antes de esto, Ashburn y Boardman salían
        # entre las "ciudades" con más visitas.
        red, es_nube = desde_centro_de_datos(ip)
        if es_nube:
            nube[red] += 1
            continue
        clave_dia = d['fecha_obj'].strftime('%Y-%m-%d')

        # Solo el 404 significa "esto no existe". Un 401 o un 403 en
        # /privado/* es la comprobación de sesión de alguien que no ha
        # entrado: funcionamiento normal, ni visita ni fallo. Contarlos
        # juntos daba una alarma falsa con rutas que sí existen.
        if estado == '404':
            fallos[ruta] += 1
            continue
        if estado.startswith('4'):
            continue

        if ESTATICOS.search(ruta):
            continue

        visitantes.add(ip)
        hits_ip[ip] += 1
        por_dia[clave_dia].add(ip)
        hits_dia[clave_dia] += 1
        horas[int(d['hora'])] += 1
        dispositivos[dispositivo(d['agente'])] += 1
        navegadores[navegador(d['agente'])] += 1

        if ruta.endswith('.html') or ruta == '/':
            paginas['Inicio' if ruta in ('/', '/index.html') else ruta.lstrip('/')] += 1
        else:
            api[ruta] += 1

        ref = d['referente']
        if ref and ref != '-' and 'subvencionesdgda' not in ref and '169.58.179.148' not in ref:
            referentes[re.sub(r'^https?://(www\.)?', '', ref).split('/')[0]] += 1

    # Geolocalización: se resuelve al final, sobre las IPs ya recogidas
    paises, ciudades = Counter(), Counter()
    lector, motivo_geo = abrir_geoip()
    if lector:
        for ip, n_hits in hits_ip.items():
            pais, ciudad = ubicacion(lector, ip)
            if pais:
                paises[pais] += n_hits
            if ciudad and pais:
                ciudades[f"{ciudad} ({pais})"] += n_hits
        lector.close()

    organizaciones = Counter()
    if resolver_dns:
        # Solo las IPs con 3 o más páginas vistas: quien pasa una vez no
        # aporta, y cada consulta es una petición de red.
        socket.setdefaulttimeout(1.5)
        cache = {}
        for ip, n_hits in hits_ip.most_common(120):
            if n_hits < 3:
                break
            org = organizacion(ip, cache)
            if org:
                organizaciones[org] += n_hits

    return dict(nube=nube, hay_asn=lector_asn is not None, paises=paises, ciudades=ciudades, motivo_geo=motivo_geo,
                organizaciones=organizaciones, robots=robots, paginas=paginas, api=api, por_dia=por_dia, hits_dia=hits_dia,
                referentes=referentes, dispositivos=dispositivos, horas=horas,
                navegadores=navegadores, fallos=fallos, visitantes=visitantes,
                descartadas=descartadas, dias=dias, total=len(filas))


# ── Presentación ─────────────────────────────────────────────────────────────

CSS = """
:root { --verde:#2E7D32; --gris:#6B7280; --borde:#E5E7EB; --fondo:#F9FAFB; }
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
.cifras { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:1rem; margin-bottom:1rem; }
.cifra { background:#fff; border:1px solid var(--borde); border-radius:8px;
         padding:1rem; }
.cifra__num { font-size:1.8rem; font-weight:700; color:var(--verde);
              line-height:1.2; }
.cifra__eti { font-size:.85rem; color:var(--gris); }
table { width:100%; border-collapse:collapse; background:#fff;
        border:1px solid var(--borde); border-radius:8px; overflow:hidden; }
th { background:var(--verde); color:#fff; text-align:left; padding:.6rem .8rem;
     font-size:.85rem; font-weight:600; }
td { padding:.55rem .8rem; border-top:1px solid var(--borde); font-size:.9rem; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.barra { background:#E8F5E9; height:8px; border-radius:4px; }
.barra > div { background:var(--verde); height:100%; border-radius:4px; }
.nota { background:#FFF7ED; border-left:3px solid #F59E0B; padding:.8rem 1rem;
        font-size:.88rem; border-radius:0 6px 6px 0; margin-top:1rem; }
.vacio { color:var(--gris); font-style:italic; padding:1rem; background:#fff;
         border:1px solid var(--borde); border-radius:8px; }
svg { background:#fff; border:1px solid var(--borde); border-radius:8px;
      max-width:100%; height:auto; }
@media (max-width:600px) { body { padding:1rem .5rem; } }

.imprimir { float:right; background:var(--verde); color:#fff; border:0;
            border-radius:6px; padding:.5rem .9rem; font-size:.85rem;
            cursor:pointer; font-family:inherit; }
.imprimir:hover { background:#1B5E20; }

/* Al imprimir o guardar como PDF: fuera el botón, y que las tablas no se
   partan por la mitad entre dos páginas. */
@media print {
  body { background:#fff; padding:0; }
  .imprimir { display:none; }
  h2 { break-after:avoid; }
  table, svg { break-inside:avoid; }
  .cifra, .nota { border:1px solid #ccc; }
}
"""


def grafico(hits_por_dia, ancho=860, alto=200):
    """Gráfica de barras en SVG, sin librerías ni conexión."""
    if not hits_por_dia:
        return '<p class="vacio">Sin datos suficientes todavía.</p>'
    dias = sorted(hits_por_dia)
    tope = max(hits_por_dia.values()) or 1
    margen, base = 40, alto - 28
    paso = (ancho - margen - 10) / len(dias)
    ancho_barra = max(3, min(paso * 0.7, 48))

    partes = [f'<svg viewBox="0 0 {ancho} {alto}" role="img" '
              f'aria-label="Visitas por día">']
    partes.append(f'<line x1="{margen}" y1="{base}" x2="{ancho-10}" y2="{base}" '
                  'stroke="#E5E7EB"/>')
    partes.append(f'<text x="4" y="16" font-size="11" fill="#6B7280">{tope}</text>')
    for i, d in enumerate(dias):
        v = hits_por_dia[d]
        h = max(1, (v / tope) * (base - 20))
        x = margen + i * paso + (paso - ancho_barra) / 2
        partes.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{ancho_barra:.1f}" '
                      f'height="{h:.1f}" fill="#2E7D32" rx="2"><title>{d}: {v}</title></rect>')
        if len(dias) <= 14 or i % max(1, len(dias)//10) == 0:
            partes.append(f'<text x="{x+ancho_barra/2:.1f}" y="{alto-8}" font-size="10" '
                          f'fill="#6B7280" text-anchor="middle">{d[8:]}/{d[5:7]}</text>')
    partes.append('</svg>')
    return ''.join(partes)


def tabla(filas, cabeceras, tope=None):
    if not filas:
        return '<p class="vacio">Nada que mostrar en este periodo.</p>'
    maximo = max((f[1] for f in filas), default=1) or 1
    out = ['<table><thead><tr>']
    out += [f'<th>{html.escape(c)}</th>' for c in cabeceras]
    out.append('</tr></thead><tbody>')
    for etiqueta, valor in filas[:tope]:
        pct = valor / maximo * 100
        out.append(
            f'<tr><td>{html.escape(str(etiqueta))}</td>'
            f'<td class="num">{valor:,}</td>'
            f'<td style="width:35%"><div class="barra">'
            f'<div style="width:{pct:.0f}%"></div></div></td></tr>'.replace(',', '.')
        )
    out.append('</tbody></table>')
    return ''.join(out)


def render(d):
    dias_con_datos = sorted(d['por_dia'])
    visitantes_dia = {k: len(v) for k, v in d['por_dia'].items()}
    media = (sum(visitantes_dia.values()) / len(visitantes_dia)) if visitantes_dia else 0
    periodo = (f"{dias_con_datos[0]} a {dias_con_datos[-1]}"
               if dias_con_datos else "sin datos")

    p = [f'<!doctype html><html lang="es"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Resumen de visitas — subvencionesdgda.org</title>',
         f'<style>{CSS}</style></head><body><div class="envoltorio">',
         '<button class="imprimir" onclick="window.print()">Guardar como PDF</button>',
         '<h1>Resumen de visitas</h1>',
         f'<p class="periodo">subvencionesdgda.org · {periodo} · '
         f'generado el {datetime.now():%d/%m/%Y a las %H:%M}</p>']

    p.append('<div class="cifras">')
    for num, eti in [(f"{len(d['visitantes']):,}".replace(',', '.'), 'Personas distintas'),
                     (f"{sum(d['hits_dia'].values()):,}".replace(',', '.'), 'Páginas vistas'),
                     (f"{media:.0f}", 'Personas al día (media)'),
                     (f"{d['descartadas']['bots']:,}".replace(',', '.'), 'Peticiones de robots'),
                     (f"{sum(d['nube'].values()):,}".replace(',', '.'), 'Desde centros de datos')]:
        p.append(f'<div class="cifra"><div class="cifra__num">{num}</div>'
                 f'<div class="cifra__eti">{eti}</div></div>')
    p.append('</div>')

    p.append('<h2>Visitas por día<span class="pista">Pasa el ratón por una barra '
             'para ver la fecha y el número exacto.</span></h2>')
    p.append(grafico(d['hits_dia']))

    p.append('<h2>Páginas más vistas<span class="pista">Solo páginas; no se '
             'cuentan imágenes, hojas de estilo ni scripts.</span></h2>')
    p.append(tabla(d['paginas'].most_common(12), ['Página', 'Visitas', '']))

    p.append('<h2>De dónde llegan<span class="pista">Enlaces externos que han '
             'traído gente. Vacío significa que entran escribiendo la dirección '
             'o desde marcadores.</span></h2>')
    p.append(tabla(d['referentes'].most_common(10), ['Procedencia', 'Visitas', '']))

    if d['paises']:
        p.append('<h2>De qué países<span class="pista">Deducido de la dirección '
                 'IP con la base GeoLite2. El país es fiable; la ciudad es '
                 'aproximada y con conexiones móviles suele señalar la salida '
                 'de la operadora, no dónde está la persona.</span></h2>')
        p.append(tabla(d['paises'].most_common(10), ['País', 'Visitas', '']))
        if d['ciudades']:
            p.append('<div style="height:1rem"></div>')
            p.append(tabla(d['ciudades'].most_common(10), ['Ciudad', 'Visitas', '']))
    elif d['motivo_geo']:
        p.append('<h2>De qué países</h2>')
        p.append(f'<p class="vacio">Sin datos de ubicación: {html.escape(d["motivo_geo"])}. '
                 'Es opcional; el resto del resumen no depende de ello.</p>')

    p.append('<h2>Con qué entran</h2>')
    p.append(tabla(d['dispositivos'].most_common(), ['Dispositivo', 'Visitas', '']))
    p.append('<div style="height:1rem"></div>')
    p.append(tabla(d['navegadores'].most_common(6), ['Navegador', 'Visitas', '']))

    p.append('<h2>Consultas a la API<span class="pista">Peticiones de datos que '
             'hace la propia web al cargar buscadores y gráficas.</span></h2>')
    p.append(tabla(d['api'].most_common(8), ['Ruta', 'Peticiones', '']))

    if d['organizaciones']:
        p.append('<h2>Administraciones públicas<span class="pista">Organismos '
                 'identificados por el nombre de su red. Son organizaciones, no '
                 'personas, y nunca se muestra la dirección. La mayoría de '
                 'administraciones navegan con conexiones comerciales corrientes '
                 'e <strong>indistinguibles de una casa</strong>: que un '
                 'ayuntamiento no aparezca aquí no significa que no haya '
                 'entrado.</span></h2>')
        p.append(tabla(d['organizaciones'].most_common(15),
                       ['Organismo', 'Páginas vistas', '']))

    p.append('<h2>Robots y buscadores<span class="pista">No cuentan como '
             'visitas, pero conviene saber quién pasa: que Google y Bing '
             'aparezcan aquí significa que están indexando la web, que es lo '
             'que hace que la gente te encuentre.</span></h2>')
    p.append(tabla(d['robots'].most_common(10), ['Quién', 'Peticiones', '']))

    if d['nube']:
        p.append('<h2>Tráfico de centros de datos<span class="pista">Peticiones '
                 'que salen de servidores alojados en la nube (Amazon, Google, '
                 'Microsoft...). No son personas leyendo la web: son rastreadores '
                 'y escáneres que, a diferencia de Googlebot, <strong>no se '
                 'identifican como robots</strong>. Se descuentan de todas las '
                 'cifras de arriba.</span></h2>')
        p.append(tabla(d['nube'].most_common(10), ['Red', 'Peticiones', '']))
    elif not d['hay_asn']:
        p.append('<h2>Tráfico de centros de datos</h2>')
        p.append('<p class="vacio">Sin la base GeoLite2-ASN no se puede separar. '
                 'Las cifras de países incluirán entonces rastreadores alojados '
                 'en la nube, que suelen encabezar la lista sin ser personas.</p>')

    p.append('<h2>Rutas que no existen<span class="pista">Casi todo son sondeos '
             'automáticos buscando ficheros de configuración: ruido normal en '
             'cualquier servidor público. Solo preocupa si aparece una página '
             '<em>tuya</em>, porque significaría un enlace roto.</span></h2>')
    p.append(tabla(d['fallos'].most_common(10), ['Ruta pedida', 'Intentos', '']))

    p.append(f'<div class="nota"><strong>Cómo leer esto.</strong> '
             f'Se han descartado {d["descartadas"]["bots"]:,} peticiones de robots '
             f'y buscadores. Las "personas distintas" se cuentan por dirección IP, '
             f'que no es lo mismo que personas: una casa o una red móvil comparten '
             f'una sola. Sirve para ver tendencias, no para contar gente exacta. '
             f'Los registros duran 30 días.</div>'.replace(',', '.'))

    p.append('</div></body></html>')
    return ''.join(p)


def main():
    ap = argparse.ArgumentParser(description="Resumen de visitas en español.")
    ap.add_argument('--dias', type=int, default=30,
                    help='Días hacia atrás a incluir (por defecto 30).')
    ap.add_argument('--organizaciones', action='store_true',
                    help='Identificar administraciones públicas por DNS inverso. '
                         'Tarda más: consulta la red por cada visitante habitual.')
    args = ap.parse_args()

    if not LOG_DIR.exists():
        raise SystemExit(f"ERROR: no existe {LOG_DIR}")

    filas, descartadas = leer(args.dias)
    if not filas:
        raise SystemExit("ERROR: no se ha reconocido ninguna línea. ¿Ha cambiado "
                         "el log_format de Nginx?")

    DESTINO.mkdir(exist_ok=True)
    salida = DESTINO / f"resumen-{datetime.now():%Y-%m-%d}.html"
    if args.organizaciones:
        print('Resolviendo nombres de red... (puede tardar un minuto)')
    datos = construir(filas, descartadas, args.dias, args.organizaciones)
    salida.write_text(render(datos), encoding='utf-8')
    print(f"Resumen generado: {salida}")
    print(f"  {len(filas):,} peticiones de personas · "
          f"{descartadas['bots']:,} de robots descartadas".replace(',', '.'))


if __name__ == '__main__':
    main()
