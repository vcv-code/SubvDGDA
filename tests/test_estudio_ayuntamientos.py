"""
Bloque del estudio de Consejos para Mascotas y la sección de cierre de la
portada.

Ambos cuentan lo mismo desde dos sitios: la ley obliga a publicar una
Estadística de Protección Animal que todavía no existe, y mientras tanto lo que
hacen los ayuntamientos solo se sabe preguntándoselo uno a uno.
"""
import re
from pathlib import Path

RECURSOS = Path("frontend/recursos.html").read_text(encoding="utf-8")
INICIO = Path("frontend/index.html").read_text(encoding="utf-8")
CSS = Path("frontend/css/styles.css").read_text(encoding="utf-8")
HOME_JS = Path("frontend/js/home.js").read_text(encoding="utf-8")


def _texto(html, desde, hasta):
    frag = html[html.index(desde):]
    frag = frag[:frag.index(hasta)]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", frag)).strip()


# ── Bloque en recursos.html ──────────────────────────────────────────────

def test_el_bloque_del_estudio_existe_con_su_logo():
    assert 'recursos-bloque--estudio' in RECURSOS
    assert "assets/img/logos/consejosmascotas.webp" in RECURSOS
    assert Path("frontend/assets/img/logos/consejosmascotas.webp").exists()


def test_el_logo_declara_sus_dimensiones():
    """Sin `width`/`height` el navegador no reserva sitio y la página da un
    salto cuando la imagen termina de cargar."""
    img = re.search(r'<img[^>]*consejosmascotas[^>]*>', RECURSOS).group(0)
    assert "width=" in img and "height=" in img
    assert "alt=" in img


def test_el_titulo_entero_enlaza_al_estudio():
    """Al retirarse el subtítulo, este es el único acceso; el logo tiene que
    entrar dentro del enlace."""
    i = RECURSOS.index('id="bloque-estudio"')
    cabecera = RECURSOS[i:RECURSOS.index("</h2>", i)]
    assert "consulta-bienestar-animal-2025" in cabecera
    assert "<img" in cabecera


def test_las_cifras_del_estudio_llevan_su_base():
    """Un porcentaje sin base engaña: el 0,4 % de convenios es sobre quienes
    contestaron esa pregunta, no sobre los 8.132 municipios."""
    texto = _texto(RECURSOS, 'recursos-estudio__datos', "</ul>")
    assert "Entre los que contestaron a esa pregunta" in texto
    assert "4.948 ayuntamientos que llegaron a contestar" in texto


def test_se_advierte_que_las_cifras_solo_cubren_lo_municipal():
    """Sin ese aviso, 302.147 recogidos parece el problema entero cuando es la
    parte que gestionan las administraciones."""
    texto = _texto(RECURSOS, 'recursos-estudio__datos', "</ul>")
    assert "protectoras, asociaciones y particulares" in texto


# ── Sección de cierre en la portada ──────────────────────────────────────

def test_la_portada_cierra_con_la_estadistica_que_falta():
    assert 'id="estadistica-titulo"' in INICIO
    texto = _texto(INICIO, 'estadistica-texto', "</section>")
    assert "Ley 7/2023" in texto
    assert "54113" in texto            # la operación en el Inventario del INE
    assert "En proyecto" in texto


def test_se_aclara_que_el_ine_no_es_el_responsable():
    """El error habitual es atribuirle al INE la recopilación; la ley se la
    atribuye al ministerio y deja al INE la coordinación del Plan."""
    texto = _texto(INICIO, 'estadistica-texto', "</section>")
    assert "no como responsable de recopilarla" in texto


def test_se_acota_que_el_avance_publicado_es_de_hogares():
    """Los 15,17 millones son animales en hogares: de la calle no dicen nada, y
    es la calle lo que la ley pone en manos de las administraciones."""
    texto = _texto(INICIO, 'estadistica-texto', "</section>")
    assert "de hogares" in texto
    assert "de lo que pasa en la calle no dice nada" in texto


def test_se_cita_a_quien_hizo_el_estudio():
    texto = _texto(INICIO, 'estadistica-texto', "</section>")
    assert "Consejos para Mascotas" in texto
    assert "https://consejosparamascotas.com/" in INICIO


def test_la_seccion_no_estira_hasta_una_pantalla_entera():
    """`.fondo-crema` lleva `min-height: 100vh` para la sección del resumen,
    que tiene tabla. Aplicada a una de solo texto dejaba media pantalla vacía
    debajo."""
    i = INICIO.index('id="estadistica-titulo"')
    seccion = INICIO[INICIO.rindex("<section", 0, i):i]
    assert "fondo-crema" not in seccion
    assert "seccion-estadistica" in seccion


def test_las_anclas_no_quedan_bajo_la_barra_fija():
    """La navegación es `position: fixed`: sin `scroll-margin-top`, saltar a un
    ancla deja el título tapado."""
    # La declaración, no el comentario que la explica: buscar la primera
    # aparición del nombre encuentra el texto del comentario y no prueba nada.
    declaracion = re.search(r"scroll-margin-top\s*:\s*([^;]+);", CSS)
    assert declaracion, "no hay ninguna declaración scroll-margin-top"
    assert "altura-nav" in declaracion.group(1), declaracion.group(1)


# ── Banner de avisos ─────────────────────────────────────────────────────

def test_el_banner_no_promete_fecha_de_publicacion():
    """Decía «cuando se publique la resolución», dando por hecho que la
    resolución trae los listados completos. No siempre es así."""
    assert "cuando podamos obtenerlos tras la resolución" in HOME_JS
    assert "estarán disponibles cuando se publique la resolución" not in HOME_JS
