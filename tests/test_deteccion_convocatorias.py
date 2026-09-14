"""
Qué convocatorias de la BDNS son las de este proyecto, y cuáles NO.

Por qué existe este test
------------------------
La búsqueda por descripción de la API BDNS no devuelve solo las convocatorias
que recoge esta web: trae también premios, certámenes artísticos y otras líneas
de subvención de la misma Dirección General. Comprobado el 13 de septiembre de
2026, la consulta de `bdns_client.py` devuelve 8 resultados para «protección
animal» y 5 para «colonias felinas», de los cuales solo 6 y 4 interesan.

Hasta ahora bastaba con que el título dijera «PROTECCI» para clasificarlo como
`epa`. Eso hacía que dos convocatorias del MISMO año cayeran en la misma clave
y la segunda pisara a la primera **sin avisar**:

    904804  PREMIOS NACIONALES A LA PROTECCIÓN ANIMAL   → pisaba la EPA 2026
    797869  Subvenciones de concesión directa …
            … refugios de protección animal             → pisaba la EPA 2024

Las consecuencias son distintas en cada lado y ninguna es visible:

  · En `bdns_lookup.py`, la carga habría escrito en la base el número, la fecha
    y el título equivocados para esos dos años.
  · En `check_bdns.py`, que INSERTA en producción, se habría dado de alta una
    convocatoria que no toca. Ahí solo lo evitaba la suerte: se recorre en
    orden de número ascendente y `state[tipo]` corta tras la primera de cada
    tipo, así que la buena entraba antes que el premio por llevar número menor
    (904714 antes que 904804). Nada lo garantiza.

Los títulos de los casos son literales de la API, no inventados.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "data_processing"))

import bdns_lookup  # noqa: E402


def _cargar_check_bdns():
    sys.modules.setdefault("pymysql", MagicMock())
    with patch("os.makedirs"), patch("logging.basicConfig"):
        spec = importlib.util.spec_from_file_location(
            "check_bdns_det", RAIZ / "docker" / "cron" / "scripts" / "check_bdns.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


check_bdns = _cargar_check_bdns()

# Títulos reales devueltos por la API el 13-09-2026.
SON_DEL_PROYECTO = [
    ("Subvenciones a entidades de protección animal 2021", "epa"),
    ("Subvenciones a entidades de protección animal 2026", "epa"),
    ("Subvenciones a entidades locales para gestión de colonias felinas 2023", "eell"),
    ("Subvenciones a entidades locales destinadas a mejorar e impulsar el control "
     "poblacional de colonias felinas, correspondiente al año 2026", "eell"),
]

NO_SON_DEL_PROYECTO = [
    "PREMIOS NACIONALES A LA PROTECCIÓN ANIMAL.",
    "IV CERTAMEN ARTÍSTICO AMIGOS DE LOS ANIMALES. MODALIDAD FOTOGRAFÍA COLONIAS FELINAS",
    "Subvenciones de concesión directa a las entidades sin ánimo de lucro que gestionen "
    "centros y refugios de protección animal. Artículo 8 del Real Decreto-ley",
    "Premios Derechos de los Animales al proyecto más innovador de experiencias",
]

DETECTORES = [
    pytest.param(bdns_lookup._detectar_tipo, id="bdns_lookup"),
    pytest.param(check_bdns.detectar_tipo, id="check_bdns"),
]


@pytest.mark.parametrize("detectar", DETECTORES)
@pytest.mark.parametrize("titulo,esperado", SON_DEL_PROYECTO)
def test_reconoce_las_convocatorias_del_proyecto(detectar, titulo, esperado):
    assert detectar(titulo) == esperado


@pytest.mark.parametrize("detectar", DETECTORES)
@pytest.mark.parametrize("titulo", NO_SON_DEL_PROYECTO)
def test_descarta_premios_certamenes_y_otras_lineas(detectar, titulo):
    assert detectar(titulo) is None, (
        f"«{titulo[:55]}…» no es una convocatoria de esta web. Clasificarla "
        "escribe datos equivocados en la base (carga) o da de alta una "
        "convocatoria que no toca (cron), y en ninguno de los dos casos se ve."
    )


@pytest.mark.parametrize("detectar", DETECTORES)
def test_tolera_entradas_vacias(detectar):
    assert detectar("") is None
    assert detectar(None) is None


def test_las_dos_copias_del_detector_coinciden():
    """La lógica está duplicada a propósito —carga y cron no comparten código—,
    así que lo único que impide que se separen es comprobarlo."""
    titulos = [t for t, _ in SON_DEL_PROYECTO] + NO_SON_DEL_PROYECTO
    discrepan = [t for t in titulos
                 if bdns_lookup._detectar_tipo(t) != check_bdns.detectar_tipo(t)]
    assert not discrepan, (
        f"bdns_lookup y check_bdns clasifican distinto: {discrepan}. "
        "Si se cambia una, hay que cambiar la otra."
    )


def test_el_indice_no_deja_que_una_convocatoria_pise_a_otra(tmp_path, capsys):
    """Segunda red: aunque el detector fallara, el índice debe avisar y quedarse
    con la primera, en vez de sobrescribir en silencio."""
    snapshot = [
        {"numeroConvocatoria": 904714, "descripcion": "Subvenciones a entidades de protección animal 2026",
         "fechaRecepcion": "2026-05-11", "anio_convocatoria": 2026, "id": 1},
        {"numeroConvocatoria": 904804, "descripcion": "Subvenciones a entidades de protección animal 2026 BIS",
         "fechaRecepcion": "2026-05-11", "anio_convocatoria": 2026, "id": 2},
    ]
    import json
    destino = tmp_path / "2026-09-13_convocatorias_proteccion_animal.json"
    destino.write_text(json.dumps(snapshot), encoding="utf-8")

    with patch.object(bdns_lookup, "BDNS_DIR", str(tmp_path)):
        indice = bdns_lookup.cargar_indice_bdns()

    assert indice[(2026, "epa")]["num_convoc"] == "904714", (
        "Debe conservarse la PRIMERA: el orden de la API es por número "
        "ascendente y la convocatoria del año se publica antes que lo demás."
    )
    assert "AVISO" in capsys.readouterr().out
