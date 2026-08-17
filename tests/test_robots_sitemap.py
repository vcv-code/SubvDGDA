"""
robots.txt y sitemap.xml.

Lo que se protege aquí es la COHERENCIA entre tres textos que dicen lo mismo
desde sitios distintos:

  · `robots.txt` — no bloquea rastreadores de IA
  · el aviso legal — concede ese permiso expresamente
  · el README — lo explica y razona

Si alguien cambia de criterio y toca solo uno, la web acabaría permitiendo
algo que su propio aviso legal prohíbe, o al revés. Esa contradicción es
difícil de ver a simple vista y fácil de comprobar aquí.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ     = Path(__file__).parent.parent
FRONT    = RAIZ / "frontend"
ROBOTS   = FRONT / "robots.txt"
SITEMAP  = FRONT / "sitemap.xml"
AVISO    = FRONT / "aviso-legal.html"
README   = RAIZ / "README.md"

DOMINIO = "https://subvencionesdgda.org"

# Páginas que NO deben indexarse: requieren cuenta o no tienen sentido suelto
PRIVADAS = {"admin.html", "privado.html", "exclusivo.html", "login.html",
            "recuperar-password.html", "reset-password.html",
            "verificar-email.html", "mantenimiento.html"}
# Páginas que existen pero no van al sitemap por su naturaleza
FUERA = PRIVADAS | {"404.html", "50x.html", "entidad.html"}


def _publicas():
    return {f.name for f in FRONT.glob("*.html")} - FUERA


# ── robots.txt ───────────────────────────────────────────────────────────────

def test_robots_existe_y_apunta_al_sitemap():
    """Sin esta línea, los buscadores tienen que adivinar dónde está."""
    t = ROBOTS.read_text(encoding="utf-8")
    assert f"Sitemap: {DOMINIO}/sitemap.xml" in t


def test_robots_no_bloquea_ningun_rastreador():
    """Decisión tomada a propósito: permitir, incluidos los de IA.

    Si algún día se bloquea alguno, hay que cambiar TAMBIÉN el aviso legal y
    el README, que hoy conceden ese permiso. Este test salta para recordarlo.
    """
    t = ROBOTS.read_text(encoding="utf-8")
    bloqueos = re.findall(r"^User-agent:\s*(\S+)", t, re.M)
    assert bloqueos == ["*"], (
        f"Hay reglas para rastreadores concretos ({bloqueos}). Si se bloquea "
        "alguno, actualiza el aviso legal y el README: ahora mismo dicen que "
        "se permite el rastreo de IA."
    )
    assert re.search(r"^Allow:\s*/\s*$", t, re.M), "Falta el Allow general"


def test_robots_mantiene_fuera_las_paginas_con_cuenta():
    t = ROBOTS.read_text(encoding="utf-8")
    prohibidas = set(re.findall(r"^Disallow:\s*/(\S+)", t, re.M))
    for p in PRIVADAS:
        assert p in prohibidas, f"{p} debería estar en Disallow: requiere cuenta"


def test_robots_no_indexa_la_api():
    """Devuelve JSON: indexarla no aporta y consume presupuesto de rastreo."""
    t = ROBOTS.read_text(encoding="utf-8")
    for ruta in ["solicitudes/", "convocatorias/", "estadisticas/", "auth/"]:
        assert f"Disallow: /{ruta}" in t


# ── sitemap.xml ──────────────────────────────────────────────────────────────

def test_sitemap_es_xml_valido():
    ET.parse(SITEMAP)


def test_sitemap_lista_todas_las_paginas_publicas():
    """Si se añade una página pública y no se anota aquí, esto falla."""
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    raiz = ET.parse(SITEMAP).getroot()
    urls = {u.find("s:loc", ns).text for u in raiz}
    en_sitemap = {u.replace(DOMINIO + "/", "") or "index.html" for u in urls}

    faltan = _publicas() - en_sitemap
    assert not faltan, f"Páginas públicas sin listar en el sitemap: {sorted(faltan)}"


def test_sitemap_no_expone_paginas_privadas():
    """Sería contradecir al propio robots.txt."""
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {u.find("s:loc", ns).text for u in ET.parse(SITEMAP).getroot()}
    for p in PRIVADAS:
        assert f"{DOMINIO}/{p}" not in urls, f"{p} no debe estar en el sitemap"


# ── Coherencia entre los tres textos ─────────────────────────────────────────

def test_el_aviso_legal_concede_el_permiso_que_robots_refleja():
    """robots.txt permite el rastreo de IA; el aviso legal debe autorizarlo.

    Sin esto, la web permitiría en la práctica algo que su licencia
    CC BY-NC-ND prohíbe sobre el papel.
    """
    t = AVISO.read_text(encoding="utf-8")
    assert "inteligencia artificial" in t.lower(), (
        "El aviso legal no menciona el permiso para IA que robots.txt concede"
    )
    assert "no comercial" in t.lower(), (
        "Debe explicarse que el permiso va más allá de la cláusula NC"
    )


def test_el_readme_explica_el_permiso_adicional():
    t = README.read_text(encoding="utf-8")
    assert "Permiso adicional" in t and "robots.txt" in t
