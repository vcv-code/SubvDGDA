"""
Canonicalización del dominio en Nginx.

El sitio respondía igual con «www» y sin él, y con `/index.html` además de `/`.
Google los trataba como páginas distintas: Search Console marcaba tres
duplicadas y llegó a indexar `http://www.subvencionesdgda.org/`. Las etiquetas
`<link rel="canonical">` ya estaban, pero son una sugerencia: mientras el
servidor devuelva 200 en las dos variantes, pueden ignorarse.
"""
import re
from pathlib import Path

CONF = Path("docker/nginx/default.conf").read_text(encoding="utf-8")


def test_existe_el_mapa_de_host_canonico():
    assert re.search(r"map\s+\$host\s+\$host_canonico\s*\{", CONF)
    # `default $host` es lo que mantiene intacto el entorno de desarrollo, donde
    # el host es «localhost» y no debe redirigir a ningún dominio.
    assert re.search(r"default\s+\$host\s*;", CONF)
    assert "www.subvencionesdgda.org  subvencionesdgda.org;" in CONF


def test_http_salta_en_un_solo_301_a_la_variante_canonica():
    """Con `$host` encadenaba dos saltos: http://www → https://www → https://."""
    assert "return 301 https://$host_canonico$request_uri;" in CONF
    assert "return 301 https://$host$request_uri;" not in CONF


def test_https_redirige_las_variantes_no_canonicas():
    assert 'if ($host != $host_canonico)' in CONF


def test_index_html_redirige_mirando_la_uri_original():
    """Con `location = /index.html` esto entra en bucle infinito.

    La directiva `index index.html` reescribe «/» a «/index.html» internamente,
    y esa reescritura vuelve a pasar por el `location`, que redirige a «/»…
    `$request_uri` no se ve afectada por las reescrituras internas.
    """
    assert re.search(r"if \(\$request_uri ~ \^/index\\\.html", CONF)
    # Solo directivas reales: la cadena aparece a propósito en el comentario que
    # explica por qué NO se usa un `location`, y no debe hacer fallar el test.
    directivas = [l.strip() for l in CONF.splitlines()
                  if l.strip() and not l.strip().startswith("#")]
    assert not any(l.startswith("location = /index.html") for l in directivas), (
        "un `location` para /index.html provoca un bucle de redirección en la portada"
    )


def test_la_redireccion_conserva_los_parametros():
    """Sin `$is_args$args` se perderían los filtros del buscador."""
    assert "return 301 /$is_args$args;" in CONF


def test_las_paginas_declaran_su_canonical_sin_www():
    """El 301 y el canonical tienen que decir lo mismo."""
    paginas = [p for p in Path("frontend").glob("*.html")
               if 'rel="canonical"' in p.read_text(encoding="utf-8")]
    assert paginas, "ninguna página declara canonical"
    for p in paginas:
        for url in re.findall(r'rel="canonical"\s+href="([^"]+)"', p.read_text(encoding="utf-8")):
            assert url.startswith("https://subvencionesdgda.org"), f"{p.name}: {url}"
            assert "//www." not in url, f"{p.name} apunta a www: {url}"
