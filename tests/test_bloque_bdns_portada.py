"""
El bloque de la portada sobre lo que la BDNS no publica.

Por qué existe este test
------------------------
Ese bloque tiene una particularidad peligrosa: la cifra la rellena JavaScript
y el párrafo **nace con el atributo `hidden`**, de modo que si algo se rompe
no aparece un hueco ni un error, simplemente no se muestra nada. Un fallo así
no se nota mirando la página: se nota meses después, cuando alguien pregunta
por qué la web ya no dice lo de los doce millones.

Los puntos de rotura reales son tres, y son los tres que se comprueban aquí:

  1. Que alguien renombre los `id` del HTML y el JS deje de encontrarlos.
  2. Que se cambie el nombre de los campos que devuelve la API
     (`concedidas`, `importe_total`) y la suma pase a dar cero.
  3. Que se toque la lista de convocatorias ya comunicadas a la BDNS sin
     entender que la cifra se calcula EXCLUYÉNDOLAS.

No se comprueba el número en sí —sale de la base de datos y cambia cada año—,
sino que la maquinaria que lo calcula sigue enchufada.
"""
from pathlib import Path

RAIZ = Path(__file__).parent.parent
INDEX = RAIZ / "frontend" / "index.html"
HOME_JS = RAIZ / "frontend" / "js" / "home.js"
ESTADISTICAS = RAIZ / "backend" / "app" / "routers" / "estadisticas.py"


def test_el_html_tiene_los_id_que_busca_el_javascript():
    html = INDEX.read_text(encoding="utf-8")
    for identificador in ("bdns-cifra", "bdns-cifra-num"):
        assert f'id="{identificador}"' in html, (
            f"Falta id=\"{identificador}\" en index.html. El bloque nace oculto: "
            "sin ese id, pintarCifraBdns() no lo encuentra y la cifra no aparece "
            "nunca, sin dar ningún error visible."
        )


def test_el_bloque_nace_oculto():
    """Para que no asome vacío mientras llega la respuesta de la API."""
    html = INDEX.read_text(encoding="utf-8")
    bloque = html[html.index('id="bdns-cifra"') - 200:html.index('id="bdns-cifra"') + 60]
    assert "hidden" in bloque, (
        "El párrafo de la cifra debe llevar `hidden`: si no, se ve un recuadro "
        "vacío hasta que responde la API, y se queda así para siempre si falla."
    )


def test_el_javascript_suma_los_campos_que_la_api_devuelve():
    """Si el endpoint renombra un campo, la cifra daría cero en silencio."""
    js = HOME_JS.read_text(encoding="utf-8")
    api = ESTADISTICAS.read_text(encoding="utf-8")
    for campo in ("concedidas", "importe_total"):
        assert campo in js, f"home.js ya no usa `{campo}` para calcular la cifra."
        assert campo in api, (
            f"El endpoint resumen-convocatorias ya no expone `{campo}`; "
            "pintarCifraBdns() sumaría undefined y la cifra saldría a cero."
        )


def test_la_convocatoria_de_2022_sigue_declarada_como_comunicada():
    """La cifra se calcula EXCLUYENDO las convocatorias ya comunicadas.

    Si esta lista se vacía por descuido, la web pasaría a afirmar que no se
    comunicó ninguna concesión, lo cual es falso: las 592 de 2022 sí están.
    """
    js = HOME_JS.read_text(encoding="utf-8")
    assert "CONVOCATORIAS_EN_BDNS" in js
    trozo = js[js.index("const CONVOCATORIAS_EN_BDNS"):]
    trozo = trozo[:trozo.index("]")]
    assert "'epa'" in trozo and "2022" in trozo, (
        "La convocatoria EPA 2022 debe seguir en CONVOCATORIAS_EN_BDNS: sus 592 "
        "concesiones SÍ se comunicaron y no pueden contarse como no comunicadas."
    )


def test_la_cifra_lleva_punto_de_millar():
    """«2030 concesiones», rodeado de años, se lee como si fuera un año.

    En español los números de cuatro cifras van sin punto de millar, así que el
    `formatearNumero` general de la página devolvería «2030». Aquí se fuerza el
    separador. Si alguien lo revierte, el dato sigue saliendo —solo que peor—,
    que es justo el tipo de cambio que no se nota.
    """
    js = HOME_JS.read_text(encoding="utf-8")
    trozo = js[js.index("function pintarCifraBdns"):]
    trozo = trozo[:trozo.index("\n}")]
    assert "useGrouping" in trozo and "always" in trozo, (
        "pintarCifraBdns debe formatear el número con `useGrouping: 'always'`; "
        "sin eso la portada dice «2030 concesiones» en vez de «2.030»."
    )


def test_la_cifra_no_se_presenta_como_el_total_absoluto():
    """Deja fuera una concesión de 2022 que tampoco llegó a la BDNS.

    El cálculo excluye la convocatoria de 2022 entera por estar comunicada, pero
    de sus 593 concedidas la BDNS solo registró 592. Decir «en total» contradice
    al párrafo siguiente de la propia página, que cuenta que falta una.
    """
    html = INDEX.read_text(encoding="utf-8")
    linea = html[html.index('id="bdns-cifra"'):]
    linea = linea[:linea.index("</li>")]
    assert "en total" not in linea, (
        "La cifra no puede presentarse como el total absoluto: excluye la "
        "concesión de 4.684,91 € que la BDNS tampoco tiene de 2022."
    )
