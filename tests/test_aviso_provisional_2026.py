"""
El aviso de la propuesta provisional EELL 2026 y su fecha de caducidad.

Por qué existe este test
------------------------
En `estadisticas-eell.html` hay un aviso con un enlace a la propuesta de
resolución provisional de la convocatoria 2026, alojada en el portal del
Ministerio. Es información útil justo ahora —la página solo llega a 2025 y
alguien que busque 2026 se queda sin nada—, pero tiene dos problemas de los
que se olvidan con el tiempo:

1. **El enlace caduca.** La propuesta provisional no se publica en el BOE
   (art. 13.4 de la Orden DSA/1352/2022: solo en el portal del Ministerio) y
   desaparece de ahí cuando sale la definitiva. Por eso hay copia propia en
   `data/raw/eell/2026/`.

2. **El aviso caduca antes.** En cuanto los datos de 2026 entren en el
   análisis, el aviso pasa a contradecir a la propia página: diría «las cifras
   llegan hasta 2025» mientras los gráficos muestran 2026. El último test de
   aquí es el que lo impide: si aparecen registros EELL de 2026 en el dataset
   y el aviso sigue puesto, falla.

Es decir, el recordatorio no es un comentario en el HTML que se pueda pasar por
alto, es un test rojo.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PAGINA = RAIZ / "frontend" / "estadisticas-eell.html"
HOME_JS = RAIZ / "frontend" / "js" / "home.js"
DATASET = RAIZ / "data" / "final" / "dataset_unificado.json"

# El ancla del aviso en la página de EELL, a la que apunta el banner de la
# portada. Si se renombra en un sitio y no en el otro, el enlace lleva al
# principio de la página en lugar de al aviso, sin dar ningún error.
ANCLA = "aviso-provisional-2026"

URL_PROVISIONAL = (
    "https://www.dsca.gob.es/sites/default/files/derechos-sociales/"
    "derechos-animales/docs/report_propuesta_provisional_concesi%C3%B3n_"
    "COLONIAS_FELINAS_26.pdf"
)


def _pagina():
    return PAGINA.read_text(encoding="utf-8")


def _home_js():
    return HOME_JS.read_text(encoding="utf-8")


def _registros_eell_2026():
    if not DATASET.exists():
        pytest.skip("no hay dataset generado en este entorno")
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    registros = datos if isinstance(datos, list) else datos.get("registros", [])
    return [r for r in registros if r.get("tipo") == "eell" and r.get("anio") == 2026]


def test_el_aviso_enlaza_el_documento_del_ministerio():
    """El enlace tiene que ser el del portal, no el de nuestra copia local:
    data/raw/ no se sirve por web, y además conviene que la gente llegue a la
    fuente original mientras siga en pie."""
    assert URL_PROVISIONAL in _pagina(), (
        "El aviso de la convocatoria 2026 ha perdido el enlace a la propuesta "
        "provisional del Ministerio."
    )


def test_el_plazo_de_alegaciones_no_se_da_como_fecha_cerrada():
    """El documento no fija una fecha, y la web no debe inventarla.

    Concede «diez días hábiles contado a partir del día siguiente al de la
    notificación», y la notificación es individual: no es pública. Según el día
    en que se notificara sale el 23 o el 26 de octubre —el 12 es Fiesta
    Nacional y cae en lunes—, y los festivos autonómicos de cada entidad pueden
    moverlo más. De ahí el «en torno al» y la advertencia de que la fecha exacta
    depende de la notificación: si alguien las quita por quedar más limpio, la
    web pasa a afirmar algo que el documento no dice.
    """
    texto = _pagina()
    assert "diez días" in texto and "hábiles" in texto, (
        "El aviso ya no explica que el plazo se cuenta en días hábiles."
    )
    assert "en torno al" in texto, (
        "El plazo de alegaciones está dado como fecha cerrada. No lo es: "
        "depende de la notificación a cada entidad."
    )
    # El HTML parte las frases en varias líneas, así que se normalizan los
    # espacios antes de buscar.
    plano = " ".join(texto.split())
    assert "no es un dato público" in plano, (
        "Falta la advertencia de que la fecha de notificación no es pública, "
        "que es la razón de que no demos una fecha exacta."
    )


def test_la_portada_menciona_la_provisional_y_enlaza_el_aviso():
    """La mención del banner de la portada y el ancla tienen que cuadrar."""
    js = _home_js()
    assert "'eell-2026'" in js, (
        "El banner de la portada ha perdido la mención a la propuesta "
        "provisional de EELL 2026."
    )
    assert ANCLA in js, "La mención de la portada no enlaza el aviso de la página EELL."
    assert f'id="{ANCLA}"' in _pagina(), (
        f"La portada enlaza #{ANCLA} pero ese id no existe en "
        "estadisticas-eell.html: el enlace llevaría al principio de la página."
    )


def test_la_portada_no_duplica_la_url_del_ministerio():
    """A propósito: el enlace del Ministerio caduca, y tenerlo en dos ficheros
    es garantía de corregir solo uno. La portada enlaza nuestra página."""
    assert URL_PROVISIONAL not in _home_js(), (
        "La URL del Ministerio se ha copiado a home.js. Debe vivir solo en "
        "estadisticas-eell.html; la portada enlaza al aviso de esa página."
    )


def test_el_aviso_deja_claro_que_es_provisional():
    """Sin esto, 35 beneficiarias se lee como un dato cerrado. No lo es: queda
    plazo de alegaciones y las propuestas pueden renunciar."""
    texto = _pagina().lower()
    assert "provisional" in texto
    # «alegar» cubre alegar y alegaciones; lo que importa es que estén las dos
    # vías por las que las cifras pueden moverse todavía.
    assert "alegar" in texto and "renunciar" in texto, (
        "El aviso no advierte de que las cifras pueden cambiar por alegaciones "
        "o renuncias; tal como queda, se lee como una resolución firme."
    )


def test_el_aviso_avisa_de_que_hay_que_retirarlo_a_mano():
    """El comentario de mantenimiento del HTML es la primera pista para quien
    cargue 2026; si se borra, el siguiente test es el que avisa, pero mejor
    que la pista siga ahí."""
    assert "MANTENIMIENTO" in _pagina()


def test_el_aviso_desaparece_cuando_2026_entra_en_el_analisis():
    """La caducidad, comprobada contra los datos y no contra el calendario.

    Mientras no haya registros EELL de 2026, el aviso debe estar. En cuanto los
    haya, sobra: la página ya muestra 2026 y el aviso diría lo contrario.
    """
    hay_datos_2026 = bool(_registros_eell_2026())
    aviso_puesto = URL_PROVISIONAL in _pagina()
    mencion_puesta = "'eell-2026'" in _home_js()

    if hay_datos_2026:
        assert not aviso_puesto, (
            "Ya hay datos EELL de 2026 cargados, así que el aviso de la "
            "propuesta provisional sobra y contradice a la página: dice que "
            "las cifras llegan hasta 2025. Hay que retirar el bloque "
            "`aviso-banner` de frontend/estadisticas-eell.html y revisar el "
            "subtítulo y el rango de años de la cabecera."
        )
        assert not mencion_puesta, (
            "Ya hay datos EELL de 2026, pero el banner de la portada sigue "
            "anunciando la propuesta provisional. Hay que quitar la entrada "
            "'eell-2026' de DOCS_PROVISIONALES en frontend/js/home.js."
        )
    else:
        assert aviso_puesto, (
            "No hay datos EELL de 2026 y tampoco está el aviso: quien busque "
            "la convocatoria de 2026 no encuentra nada en esta página."
        )
