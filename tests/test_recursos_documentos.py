"""
Bloque «Guías y documentos útiles» de recursos.html.

Cada entrada es UN PÁRRAFO: título enlazado, dos puntos y la descripción
seguida. Ni tarjetas ni etiqueta de tipo: la sección ocupaba demasiado para lo
que aporta —son enlaces con contexto, no fichas— y la lista va a crecer.
"""
import re
from pathlib import Path

HTML = Path("frontend/recursos.html").read_text(encoding="utf-8")
CSS = Path("frontend/css/styles.css").read_text(encoding="utf-8")


def _bloque_lista():
    ini = HTML.index('<ul class="lista-documentos">')
    return HTML[ini:HTML.index("</ul>", ini)]


def _texto_plano():
    """El bloque sin etiquetas y con los espacios normalizados.

    Las comprobaciones de CONTENIDO van contra esto y no contra el HTML crudo:
    una frase puede quedar partida en dos líneas por el ajuste de ancho, o con
    un `<strong>` en medio, y seguir siendo la misma frase para quien la lee.
    """
    import re
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", _bloque_lista())).strip()


def test_los_documentos_van_en_listado():
    assert '<ul class="lista-documentos">' in HTML
    assert "card-guia" not in HTML, "quedan restos de las tarjetas anteriores"


def test_cada_documento_tiene_titulo_enlazado_y_descripcion():
    bloque = _bloque_lista()
    items = bloque.count('class="lista-documentos__item"')
    assert items >= 7, f"solo {items} documentos"
    assert bloque.count('class="lista-documentos__titulo"') == items
    # Los dos puntos unen título y descripción en una sola frase.
    assert bloque.count("</a>:") == items


def test_no_quedan_etiquetas_de_tipo():
    """Se retiraron: «Documento oficial · PDF» ocupaba una línea por entrada
    sin aportar nada que el propio título no diga."""
    assert "lista-documentos__tipo" not in HTML
    assert "lista-documentos__tipo" not in CSS


def test_la_plantilla_propia_se_sirve_desde_el_sitio():
    """No es un enlace a otra web: es un PDF alojado aquí, para descargar y
    completar."""
    assert "assets/docs/propuesta-contratacion-pienso-colonias-felinas.pdf" in HTML
    assert Path(
        "frontend/assets/docs/propuesta-contratacion-pienso-colonias-felinas.pdf"
    ).exists()


def test_los_enlaces_externos_no_exponen_la_pagina():
    """`target="_blank"` sin `rel="noopener"` deja que la pestaña abierta
    manipule la de origen."""
    for url, atributos in re.findall(
            r'<a href="(https?://[^"]+)"\s*([^>]*)>', _bloque_lista()):
        assert 'target="_blank"' in atributos, url
        assert "noopener" in atributos, url


def test_los_estilos_de_la_lista_existen():
    for clase in ("lista-documentos", "lista-documentos__item",
                  "lista-documentos__titulo"):
        assert f".{clase} " in CSS or f".{clase}:" in CSS or f".{clase}\n" in CSS, clase
    assert ".card-guia" not in CSS, "estilos huérfanos de las tarjetas"


def test_los_enlaces_dentro_de_una_descripcion_se_ven_pulsables():
    """Los <a> globales van sin subrayado y con color heredado: dentro de un
    párrafo pasarían por texto corriente."""
    i = CSS.index(".lista-documentos__item a:not(.lista-documentos__titulo) {")
    bloque = CSS[i:CSS.index("}", i)]
    assert "text-decoration" in bloque and "underline" in bloque


def test_ninguna_url_esta_partida_en_dos_lineas():
    """Un `href` con un salto de línea dentro deja el enlace roto.

    El navegador elimina el salto pero NO los espacios de la sangría, que
    acaban dentro de la dirección. No da error en ninguna parte: simplemente
    lleva a una página que no existe. Pasó al ajustar el ancho del texto
    automáticamente, así que las URLs van siempre en una sola línea.
    """
    for href in re.findall(r'href\s*=\s*"([^"]*)"', _bloque_lista()):
        assert "\n" not in href, f"URL partida en dos líneas: {href[:60]}…"
        assert " " not in href, f"URL con espacios: {href[:60]}…"


def test_se_distingue_la_via_estatal_de_la_autonomica():
    """Cada comunidad tiene su portal y su órgano de garantía. Sin decirlo,
    alguien reclama donde no toca y pierde el plazo."""
    texto = _texto_plano()
    assert "Portal de Transparencia del Estado" in texto
    assert "comunidad autónoma o a un ayuntamiento" in texto
    assert "órganos de garantía" in texto


def test_se_distingue_reclamar_de_quejarse():
    """Una reclamación de transparencia y una queja al Defensor del Pueblo
    sirven para cosas distintas, y se confunden con facilidad."""
    texto = _texto_plano()
    assert "Consejo de Transparencia y Buen Gobierno" in texto
    assert "Defensor del Pueblo" in texto
    assert "no son lo mismo" in texto


# PDF que sirve esta web, en vez de enlazarlos fuera. La mayoría son propios;
# el de FDCats se aloja con permiso de uso divulgativo y con su origen citado en
# la propia entrada, porque un enlace a otra web se muere cuando la reorganizan
# —que es justo lo que pasó con la ficha de GEMFE en AVEPA—.
DOCUMENTOS_ALOJADOS = (
    "plan-accion-2026-2030-colonias-felinas-resumen.pdf",
    "gestion-etica-colonias-felinas-proyectos-cer.pdf",
)


def test_el_documento_ajeno_cita_su_origen():
    """Se aloja un PDF de FDCats en vez de enlazarlo. Servir el trabajo de otra
    entidad sin decir de dónde sale es apropiárselo, aunque no se pretenda."""
    bloque = _bloque_lista()
    assert "assets/docs/gestion-etica-colonias-felinas-proyectos-cer.pdf" in bloque
    assert "fdcats.com" in bloque, "falta el enlace a la web de origen"


def test_los_documentos_alojados_estan_enlazados_y_existen():
    """Si el fichero no sube al repo, el enlace da un 404 y nadie se entera
    hasta que alguien lo pulsa: no hay error en consola ni en el servidor."""
    bloque = _bloque_lista()
    for nombre in DOCUMENTOS_ALOJADOS:
        assert f"assets/docs/{nombre}" in bloque, f"{nombre} no está enlazado"
        ruta = Path("frontend/assets/docs") / nombre
        assert ruta.exists(), f"falta el fichero {ruta}"
        assert ruta.stat().st_size > 50_000, f"{nombre} pesa sospechosamente poco"
        assert ruta.read_bytes()[:5] == b"%PDF-", f"{nombre} no es un PDF"
