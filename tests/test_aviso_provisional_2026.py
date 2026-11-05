"""
Los avisos de las propuestas provisionales de 2026 y su fecha de caducidad.

Por qué existe este test
------------------------
`estadisticas-eell.html` y `estadisticas-epas.html` llevan un aviso con las
cifras de la propuesta de resolución provisional de la convocatoria 2026 de su
línea. Es información útil justo ahora —las páginas solo llegan a 2025 y quien
busque 2026 se queda sin nada—, pero caduca sola y de dos maneras distintas:

1. **El aviso contradice a su página.** En cuanto los datos de 2026 entren en el
   análisis, el texto diría «las cifras llegan hasta 2025» mientras los gráficos
   muestran 2026.

2. **El enlace de EELL caduca.** Su propuesta provisional no va al BOE —el art.
   13.4 de la Orden DSA/1352/2022 solo obliga a publicarla en el portal del
   Ministerio— y desaparece de ahí al salir la definitiva. Por eso hay copia
   propia en `data/raw/eell/2026/`. El de EPA no tiene ese problema: su
   propuesta se publica en la BDNS y la ficha de la convocatoria acumula
   documentos.

Esa diferencia entre las dos líneas no es un detalle: son órdenes de bases
distintas, y de ahí sale también que el plazo de alegaciones de EPA sea
calculable (corre desde la publicación, que es pública) y el de EELL no (corre
desde la notificación a cada entidad, que no lo es).

El último test es el que convierte el recordatorio en algo que no se puede pasar
por alto: no mira el calendario, mira los datos.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
HOME_JS = RAIZ / "frontend" / "js" / "home.js"
DATASET = RAIZ / "data" / "final" / "dataset_unificado.json"

URL_EELL = (
    "https://www.dsca.gob.es/sites/default/files/derechos-sociales/"
    "derechos-animales/docs/report_propuesta_provisional_concesi%C3%B3n_"
    "COLONIAS_FELINAS_26.pdf"
)
URL_EPA = "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/904714"

# tipo -> (página, ancla, clave en DOCS_PROVISIONALES, enlace que debe llevar)
AVISOS = {
    "eell": ("estadisticas-eell.html", "aviso-provisional-2026", "eell-2026", URL_EELL),
    "epa":  ("estadisticas-epas.html", "aviso-provisional-epa-2026", "epa-2026", URL_EPA),
}


def _pagina(tipo):
    return (RAIZ / "frontend" / AVISOS[tipo][0]).read_text(encoding="utf-8")


def _home_js():
    return HOME_JS.read_text(encoding="utf-8")


def _registros_2026(tipo):
    if not DATASET.exists():
        pytest.skip("no hay dataset generado en este entorno")
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    registros = datos if isinstance(datos, list) else datos.get("registros", [])
    return [r for r in registros if r.get("tipo") == tipo and r.get("anio") == 2026]


# ── Lo que vale para los dos avisos ──────────────────────────────────────

@pytest.mark.parametrize("tipo", sorted(AVISOS))
def test_el_aviso_enlaza_el_documento_oficial(tipo):
    """Nunca a la copia de `data/raw/`: no se sirve por web, y conviene que la
    gente llegue a la fuente original."""
    _, _, _, url = AVISOS[tipo]
    assert url in _pagina(tipo), f"El aviso de {tipo.upper()} ha perdido su enlace oficial."


@pytest.mark.parametrize("tipo", sorted(AVISOS))
def test_el_aviso_deja_claro_que_es_provisional(tipo):
    """Sin esto, las cifras se leen como un dato cerrado. No lo son."""
    texto = _pagina(tipo).lower()
    assert "provisional" in texto
    assert "alegar" in texto, (
        f"El aviso de {tipo.upper()} no advierte de que las cifras pueden cambiar "
        "por alegaciones; tal como queda, se lee como una resolución firme."
    )


@pytest.mark.parametrize("tipo", sorted(AVISOS))
def test_el_aviso_avisa_de_que_hay_que_retirarlo_a_mano(tipo):
    assert "MANTENIMIENTO" in _pagina(tipo)


@pytest.mark.parametrize("tipo", sorted(AVISOS))
def test_la_portada_menciona_el_aviso_y_el_ancla_cuadra(tipo):
    """Un ancla mal escrita lleva al principio de la página sin dar error."""
    _, ancla, clave, _ = AVISOS[tipo]
    js = _home_js()
    assert f"'{clave}'" in js, f"El banner de la portada ha perdido la mención de {tipo.upper()}."
    assert ancla in js, f"La mención de {tipo.upper()} no enlaza el aviso de su página."
    assert f'id="{ancla}"' in _pagina(tipo), (
        f"La portada enlaza #{ancla} pero ese id no existe en {AVISOS[tipo][0]}."
    )


@pytest.mark.parametrize("tipo", sorted(AVISOS))
def test_el_aviso_desaparece_cuando_2026_entra_en_el_analisis(tipo):
    """La caducidad, comprobada contra los datos y no contra el calendario."""
    _, _, clave, url = AVISOS[tipo]
    hay_datos = bool(_registros_2026(tipo))
    aviso_puesto = url in _pagina(tipo)
    mencion_puesta = f"'{clave}'" in _home_js()

    if hay_datos:
        assert not aviso_puesto, (
            f"Ya hay datos {tipo.upper()} de 2026 cargados, así que el aviso de la "
            "propuesta provisional sobra y contradice a la página: dice que las "
            f"cifras llegan hasta 2025. Hay que retirar el bloque `aviso-banner` de "
            f"frontend/{AVISOS[tipo][0]} y revisar el subtítulo y el rango de años."
        )
        assert not mencion_puesta, (
            f"Ya hay datos {tipo.upper()} de 2026, pero el banner de la portada sigue "
            f"anunciando la propuesta provisional: quitar '{clave}' de "
            "DOCS_PROVISIONALES en frontend/js/home.js."
        )
    else:
        assert aviso_puesto, (
            f"No hay datos {tipo.upper()} de 2026 y tampoco está el aviso: quien busque "
            "la convocatoria de 2026 no encuentra nada en esa página."
        )


# ── Lo propio de cada línea ──────────────────────────────────────────────

def test_el_plazo_de_eell_no_se_da_como_fecha_cerrada():
    """El documento de EELL no fija fecha: concede «diez días hábiles contado a
    partir del día siguiente al de la notificación», y la notificación es
    individual y no pública. Según el día sale el 23 o el 26 de octubre, y los
    festivos autonómicos pueden moverlo. Si alguien lo "limpia" a una fecha
    cerrada, la web afirma algo que el documento no dice."""
    plano = " ".join(_pagina("eell").split())
    assert "diez días" in plano and "hábiles" in plano
    assert "en torno al" in plano, (
        "El plazo de alegaciones de EELL está dado como fecha cerrada. No lo es: "
        "depende de la notificación a cada entidad."
    )
    assert "no es un dato público" in plano, (
        "Falta la advertencia de que la fecha de notificación no es pública, que "
        "es la razón de que no demos una fecha exacta."
    )


def test_el_plazo_de_epa_se_da_cerrado_porque_se_puede():
    """Aquí sería un exceso de cautela no dar la fecha.

    El plazo de EPA corre desde la publicación en la BDNS, y esa fecha es
    pública: la propia BDNS la expone en
    `GET /bdnstrans/api/convocatorias?vpd=GE&numConv=904714`, donde el documento
    «Propuesta provisional de Resolución de concesión» lleva
    `datPublicacion: 2026-11-04`. Diez días hábiles desde el día siguiente, sin
    festivos nacionales por medio, dan el miércoles 18 de noviembre.
    """
    plano = " ".join(_pagina("epa").split())
    assert "diez días" in plano and "hábiles" in plano
    assert "18 de noviembre de 2026" in plano, (
        "El aviso de EPA ha perdido el vencimiento del plazo de alegaciones."
    )
    assert "en torno al" not in plano, (
        "El plazo de EPA se ha vuelto aproximado. No hace falta: su fecha de "
        "publicación es pública, al contrario que la notificación de EELL."
    )


def test_la_portada_no_duplica_las_urls_de_los_documentos():
    """A propósito: la de EELL caduca, y tenerla en dos ficheros es garantía de
    corregir solo uno. La portada enlaza nuestras páginas."""
    js = _home_js()
    for url in (URL_EELL, URL_EPA):
        assert url not in js, (
            "Una URL de documento se ha copiado a home.js. Deben vivir solo en su "
            "página; la portada enlaza al aviso de cada una."
        )
