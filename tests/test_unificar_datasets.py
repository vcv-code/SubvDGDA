"""
Tests unitarios para las funciones de normalización de unificar_datasets.py.

Se prueban las transformaciones puras (sin I/O ni BD): normalización de
estados EPA y EELL, limpieza de importes, entidades y puntuaciones.
"""
import pytest
from scripts.data_processing.unificar_datasets import (
    normalizar_estado_epa,
    normalizar_estado_eell,
    limpiar_importe,
    limpiar_entidad,
    limpiar_puntuacion,
    limpiar_estado,
    indexar_solicitudes_epa,
    resolver_anio_epa,
    corregir_identidad,
    CIF_CORREGIDO,
    NOMBRE_CORREGIDO,
    CIF_AUSENTE,
)


# ─────────────────────────────────────────────
# normalizar_estado_epa
# El BOE llama "denegada" a dos realidades distintas según el año.
# ─────────────────────────────────────────────

def test_denegada_hasta_2023_es_excluida():
    assert normalizar_estado_epa("denegada", 2021) == "excluida"
    assert normalizar_estado_epa("denegada", 2022) == "excluida"
    assert normalizar_estado_epa("denegada", 2023) == "excluida"

def test_denegada_desde_2024_es_no_beneficiaria():
    assert normalizar_estado_epa("denegada", 2024) == "no_beneficiaria"
    assert normalizar_estado_epa("denegada", 2025) == "no_beneficiaria"

def test_otros_estados_epa_no_cambian():
    for estado in ("concedida", "excluida", "desistida", "no_beneficiaria"):
        assert normalizar_estado_epa(estado, 2024) == estado
        assert normalizar_estado_epa(estado, 2021) == estado


# ─────────────────────────────────────────────
# normalizar_estado_eell
# Concedida con importe 0 → no_beneficiaria (datos PDF sin importe real).
# ─────────────────────────────────────────────

def test_concedida_sin_importe_es_no_beneficiaria():
    assert normalizar_estado_eell("concedida", 0.0) == "no_beneficiaria"
    assert normalizar_estado_eell("concedida", None) == "no_beneficiaria"

def test_concedida_con_importe_permanece():
    assert normalizar_estado_eell("concedida", 5000.0) == "concedida"

def test_otros_estados_eell_no_cambian():
    for estado in ("excluida", "desistida", "no_beneficiaria"):
        assert normalizar_estado_eell(estado, 0.0) == estado


# ─────────────────────────────────────────────
# limpiar_importe
# ─────────────────────────────────────────────

def test_importe_none_da_cero():
    assert limpiar_importe(None) == 0.0

def test_importe_string_vacio_da_cero():
    assert limpiar_importe("") == 0.0

def test_importe_float_valido():
    assert limpiar_importe(3445.36) == 3445.36

def test_importe_entero():
    assert limpiar_importe(1000) == 1000.0

def test_importe_no_parseable_da_cero():
    assert limpiar_importe("no es un número") == 0.0


# ─────────────────────────────────────────────
# limpiar_entidad
# ─────────────────────────────────────────────

def test_entidad_none_da_none():
    assert limpiar_entidad(None) is None

def test_entidad_vacia_da_none():
    assert limpiar_entidad("") is None
    assert limpiar_entidad("   ") is None

def test_entidad_none_string_da_none():
    assert limpiar_entidad("None") is None

def test_entidad_normal_queda_igual():
    assert limpiar_entidad("  Asociación Gatos Madrid  ") == "Asociación Gatos Madrid"


# ─────────────────────────────────────────────
# limpiar_puntuacion
# ─────────────────────────────────────────────

def test_puntuacion_none_da_none():
    assert limpiar_puntuacion(None) is None

def test_puntuacion_float():
    assert limpiar_puntuacion(76.5) == 76.5

def test_puntuacion_no_numerica_da_none():
    assert limpiar_puntuacion("no válido") is None


# ─────────────────────────────────────────────
# limpiar_estado
# ─────────────────────────────────────────────

def test_estado_none_da_none():
    assert limpiar_estado(None) is None

def test_estado_vacio_da_none():
    assert limpiar_estado("") is None

def test_estado_normaliza_a_minusculas():
    assert limpiar_estado("Concedida") == "concedida"
    assert limpiar_estado("EXCLUIDA") == "excluida"


# ─────────────────────────────────────────────
# resolver_anio_epa
# Resoluciones tardías: una solicitud del año N cuya resolución no se publica
# hasta el BOE de N+1 debe atribuirse a la convocatoria N, no al fichero N+1.
# Solo se reatribuye si el mismo expediente Y el mismo CIF están en el año N.
# ─────────────────────────────────────────────

@pytest.fixture
def indice_epa():
    """Réplica reducida del dataset real con los cuatro casos cross-year."""
    return indexar_solicitudes_epa({
        2021: [
            # El BOE de 2021 publica un expediente numerado como 2022...
            {"num_expediente": "SUBV2022021", "cif": "G01779131"},
            # ...y otro con errata de año en el número (2032).
            {"num_expediente": "SUBV2032021", "cif": "G98657232"},
        ],
        2022: [
            # Mismo número que en 2021 pero OTRA entidad: el BOE lo reutilizó.
            {"num_expediente": "SUBV2022021", "cif": "G66561812"},
            {"num_expediente": "SUBV2022659", "cif": "G90180365"},
        ],
        2023: [
            {"num_expediente": "2023B628", "cif": "G45844933"},
            # Resolución tardía del expediente de 2022, misma entidad.
            {"num_expediente": "SUBV2022659", "cif": "G90180365"},
        ],
        2024: [
            # Resolución tardía del expediente de 2023, misma entidad.
            {"num_expediente": "2023B628", "cif": "G45844933"},
        ],
    })


def test_anio_declarado_igual_al_fichero_no_cambia(indice_epa):
    item = {"anio": 2023, "num_expediente": "2023B628", "cif": "G45844933"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2023

def test_sin_anio_declarado_usa_el_del_fichero(indice_epa):
    item = {"anio": None, "num_expediente": "LO_QUE_SEA", "cif": "G00000000"}
    assert resolver_anio_epa(item, 2025, indice_epa) == 2025

def test_resolucion_tardia_se_reatribuye_a_su_convocatoria(indice_epa):
    """La Sexta Huella: expediente de 2022 resuelto en el BOE de 2023."""
    item = {"anio": 2022, "num_expediente": "SUBV2022659", "cif": "G90180365"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2022

def test_resolucion_tardia_de_2023_resuelta_en_2024(indice_epa):
    """Amibichos: expediente de 2023 resuelto en el BOE de 2024."""
    item = {"anio": 2023, "num_expediente": "2023B628", "cif": "G45844933"}
    assert resolver_anio_epa(item, 2024, indice_epa) == 2023

def test_numero_reutilizado_por_otra_entidad_no_se_reatribuye(indice_epa):
    """SUBV2022021: mismo número en 2021 y 2022 pero CIF distinto.

    Es el falso positivo que justifica comprobar el CIF: sin esa comprobación
    ambas entidades colapsarían bajo la misma clave de deduplicación.
    """
    item = {"anio": 2022, "num_expediente": "SUBV2022021", "cif": "G01779131"}
    assert resolver_anio_epa(item, 2021, indice_epa) == 2021

def test_anio_con_errata_no_se_reatribuye(indice_epa):
    """SUBV2032021: declara 2032, año para el que no hay fichero."""
    item = {"anio": 2032, "num_expediente": "SUBV2032021", "cif": "G98657232"}
    assert resolver_anio_epa(item, 2021, indice_epa) == 2021

def test_mismo_expediente_distinto_cif_no_se_reatribuye(indice_epa):
    """Aunque el año declarado exista, si el CIF no casa se queda en su fichero."""
    item = {"anio": 2022, "num_expediente": "SUBV2022659", "cif": "G99999999"}
    assert resolver_anio_epa(item, 2023, indice_epa) == 2023

def test_indice_agrupa_por_anio_de_fichero(indice_epa):
    assert ("SUBV2022659", "G90180365") in indice_epa[2022]
    assert ("SUBV2022659", "G90180365") not in indice_epa[2021]


# ─────────────────────────────────────────────
# corregir_identidad
# Erratas del BOE verificadas contra fuentes oficiales. Sin estas correcciones
# la entidad sale partida en dos fichas y su histórico se ve incompleto.
# ─────────────────────────────────────────────

def test_gat_i_cua_2024_se_une_a_los_demas_anios():
    """El BOE de 2024 transpuso dos dígitos: …37041 -> …34071."""
    cif, nombre, corregido = corregir_identidad("G16734071", "ASSOCIACIÓ GAT I CUA", 2024)
    assert cif == "G16737041"
    assert corregido is True

def test_gat_i_cua_queda_con_una_sola_grafia():
    """Los cuatro años tienen que dar el mismo nombre, no dos."""
    grafias = {
        corregir_identidad(c, n, a)[1]
        for c, n, a in [("G16737041", "ASSOCIACION GAT I CUA", 2022),
                        ("G16737041", "ASSOCIACION GAT I CUA", 2023),
                        ("G16734071", "ASSOCIACIÓ GAT I CUA", 2024),
                        ("G16737041", "ASSOCIACION GAT I CUA", 2025)]
    }
    assert grafias == {"ASSOCIACIÓ GAT I CUA"}

def test_gatos_de_el_puerto_unifica_el_nif_rectificado():
    cif, nombre, _ = corregir_identidad("G72307358", "GATOS DEL PUERTO", 2022)
    assert cif == "G72296254"
    assert nombre == 'ASOCIACIÓN "GATOS DE EL PUERTO"'

def test_cocoa_recupera_el_cif_que_faltaba_en_2021():
    cif, _, corregido = corregir_identidad(None, "LAS ALMAS DE COCOA", 2021)
    assert cif == "G67811000"
    assert corregido is True

def test_cocoa_sin_cif_solo_se_rellena_en_su_anio():
    """La tabla va por (nombre, año) para no asignar a ciegas a un homónimo."""
    assert corregir_identidad(None, "LAS ALMAS DE COCOA", 2030)[0] is None

def test_municipios_con_el_nombre_mal_en_el_boe():
    """El CIF es correcto —y por eso la provincia ya salía bien—, el nombre no."""
    assert corregir_identidad("P4608700C", "AYUNTAMIENTO DE CASAVIEJA", 2023)[1] == \
        "AYUNTAMIENTO DE CARLET"
    assert corregir_identidad("P1303100J", "AYUNTAMIENTO DE CASTILFORTE", 2023)[1] == \
        "AYUNTAMIENTO DE CARRIÓN DE CALATRAVA"

def test_los_municipios_reales_no_se_tocan():
    """Casavieja (Ávila) y Castilforte (Guadalajara) existen y tienen su propio CIF."""
    assert corregir_identidad("P0505400B", "AYUNTAMIENTO DE CASAVIEJA", 2025) == \
        ("P0505400B", "AYUNTAMIENTO DE CASAVIEJA", False)
    assert corregir_identidad("P1909200F", "AYUNTAMIENTO DE CASTILFORTE", 2024) == \
        ("P1909200F", "AYUNTAMIENTO DE CASTILFORTE", False)

def test_una_entidad_cualquiera_pasa_intacta():
    assert corregir_identidad("G12345678", "PROTECTORA X", 2024) == \
        ("G12345678", "PROTECTORA X", False)
    assert corregir_identidad(None, "SIN CIF NI TABLA", 2024) == \
        (None, "SIN CIF NI TABLA", False)

def test_las_tablas_no_se_pisan_entre_si():
    """Un CIF corregido no puede ser a su vez clave de otra corrección."""
    assert not set(CIF_CORREGIDO.values()) & set(CIF_CORREGIDO)

def test_torrevieja_lleva_g_por_ser_asociacion():
    """Inscrita en el Registro de Asociaciones de Alicante: una asociación no
    puede tener un NIF con «B», que es de sociedad limitada."""
    cif, _, corregido = corregir_identidad(
        "B54999156", "ASOCIACIÓN PROYECTO CES GATOS TORREVIEJA", 2024)
    assert cif == "G54999156"
    assert corregido is True

def test_leperos_adopta_el_cif_de_la_publicacion_mas_reciente():
    """Único caso sin fuente externa: se adopta el de 2025 a conciencia."""
    assert corregir_identidad("G56705338", "SOS PELUDOS LEPEROS", 2024)[0] == \
        "G56725328"

def test_ningun_cif_corregido_apunta_a_otro_corregido():
    """Una corrección no puede encadenarse con otra: el resultado sería
    dependiente del orden y silenciosamente inestable."""
    assert not set(CIF_CORREGIDO.values()) & set(CIF_CORREGIDO)


# ─────────────────────────────────────────────
# Ubicación en la interfaz
# Los municipios que el BOE nombra abreviados («Burguillos», «La Mata», «El
# Cuervo», «La Frontera») existen en más de una provincia. No son erratas y no
# se corrigen: se desambiguan mostrando la provincia, que ya viene del CIF.
# ─────────────────────────────────────────────

def test_la_ficha_de_entidad_tiene_hueco_para_la_ubicacion():
    from pathlib import Path
    html = Path("frontend/entidad.html").read_text(encoding="utf-8")
    assert 'id="entidad-ubicacion"' in html
    assert 'id="entidad-provincia"' in html
    js = Path("frontend/js/entidad.js").read_text(encoding="utf-8")
    assert "s.provincia" in js

def test_el_modal_del_buscador_muestra_provincia_y_no_solo_ccaa():
    from pathlib import Path
    js = Path("frontend/js/modal-entidad.js").read_text(encoding="utf-8")
    assert "conUbic.provincia" in js
    html = Path("frontend/buscador.html").read_text(encoding="utf-8")
    assert "Ubicación" in html


# ─────────────────────────────────────────────
# Periodo subvencionable
# El año que financia una convocatoria NO es el suyo: las EPA de 2021-2024 y
# todas las EELL pagan gastos del año siguiente. Es la confusión que la columna
# «Periodo subvencionable» de la portada existe para deshacer.
# ─────────────────────────────────────────────

def test_la_eell_de_2023_es_semestral_no_anual():
    """Su extracto fija «entre el 1 de octubre de 2023 y el 31 de marzo del año
    2024»: seis meses. Durante mucho tiempo se dio por hecho que todas las EELL
    eran anuales."""
    from scripts.data_processing.cargar_dataset import _PERIODO_SUBVENCIONABLE
    assert _PERIODO_SUBVENCIONABLE[(2023, "eell")][0] == 6

def test_los_semestres_de_2024_son_epa_2023_y_epa_2024():
    from scripts.data_processing.cargar_dataset import _PERIODO_SUBVENCIONABLE
    assert _PERIODO_SUBVENCIONABLE[(2023, "epa")][1:] == ("2024", "1.er semestre")
    assert _PERIODO_SUBVENCIONABLE[(2024, "epa")][1:] == ("2024", "2.º semestre")

def test_ninguna_convocatoria_epa_financio_2021():
    """Consecuencia del desfase que sorprende a quien mira la tabla."""
    from scripts.data_processing.cargar_dataset import _PERIODO_SUBVENCIONABLE
    financiados = {v[1] for (a, t), v in _PERIODO_SUBVENCIONABLE.items() if t == "epa"}
    assert "2021" not in financiados

def test_la_eell_de_2026_no_declara_periodo():
    """Su extracto no fija ventana de gasto. Deducirla sería inventar."""
    from scripts.data_processing.cargar_dataset import _PERIODO_SUBVENCIONABLE
    assert _PERIODO_SUBVENCIONABLE[(2026, "eell")][1] is None

def test_periodo_meses_deriva_de_la_tabla_unica():
    """_PERIODO no puede desincronizarse de _PERIODO_SUBVENCIONABLE."""
    from scripts.data_processing.cargar_dataset import _PERIODO, _PERIODO_SUBVENCIONABLE
    assert _PERIODO == {k: v[0] for k, v in _PERIODO_SUBVENCIONABLE.items()}

def test_la_portada_pinta_la_columna_de_periodo():
    from pathlib import Path
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    assert html.count("Periodo subvencionable</th>") == 2      # EPA y EELL
    assert "Fecha de convocatoria" not in html                 # sin artículos
    js = Path("frontend/js/home.js").read_text(encoding="utf-8")
    assert "c.periodo_anio" in js and "convoc-periodo__matiz" in js

def test_las_cabeceras_pueden_partirse_en_movil():
    """Con cinco columnas, `nowrap` en las cabeceras desborda la tabla."""
    from pathlib import Path
    css = Path("frontend/css/styles.css").read_text(encoding="utf-8")
    movil = css[css.index(".tabla-wrapper .tabla-convoc th"):][:220]
    assert "nowrap" not in movil


def test_el_cron_y_el_pipeline_no_se_desincronizan():
    """`check_bdns.py` corre en su propio contenedor y no comparte código con el
    pipeline, así que duplica la tabla de periodos. Los años que ambos conocen
    tienen que coincidir, o una convocatoria mostraría un periodo distinto según
    quién la insertara."""
    import ast
    from pathlib import Path
    from scripts.data_processing.cargar_dataset import _PERIODO_SUBVENCIONABLE as pipeline

    fuente = Path("docker/cron/scripts/check_bdns.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    cron = next(
        ast.literal_eval(n.value)
        for n in arbol.body
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", None) == "_PERIODO_SUBVENCIONABLE" for t in n.targets)
    )
    comunes = set(cron) & set(pipeline)
    assert comunes, "el cron no conoce ningún año del pipeline"
    for clave in comunes:
        assert cron[clave] == pipeline[clave], f"{clave} difiere entre cron y pipeline"
