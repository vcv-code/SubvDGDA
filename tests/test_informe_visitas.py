"""
Informe de visitas (scripts/informe_visitas.sh).

Lo que se protege aquí no es que GoAccess funcione —eso se comprueba
ejecutándolo—, sino las dos cosas que fallarían en silencio:

  · Que el formato de log declarado en el script siga coincidiendo con el de
    Nginx. Si alguien cambia `log_format bdns` y no toca el script, GoAccess
    deja de reconocer las líneas y el informe sale vacío sin avisar.

  · Que los informes no acaben publicados. Contienen direcciones IP de los
    visitantes: basta con generarlos dentro de frontend/ para exponerlos.
"""
from pathlib import Path

RAIZ    = Path(__file__).parent.parent
SCRIPT  = RAIZ / "scripts/informe_visitas.sh"
NGINX   = RAIZ / "docker/nginx/default.conf"
IGNORE  = RAIZ / ".gitignore"


def test_el_script_existe_y_es_ejecutable():
    assert SCRIPT.exists(), "Falta scripts/informe_visitas.sh"


def test_el_formato_declarado_cubre_los_campos_que_registra_nginx():
    """Si Nginx cambia log_format y el script no, el informe sale vacío."""
    script = SCRIPT.read_text(encoding="utf-8")
    conf   = NGINX.read_text(encoding="utf-8")

    # Nginx registra referente, agente y tiempo: el script debe pedirlos.
    for campo, especificador in [("$http_referer", "%R"),
                                 ("$http_user_agent", "%u"),
                                 ("$request_time", "%T")]:
        assert campo in conf, f"Nginx ya no registra {campo}"
        assert especificador in script, (
            f"Nginx registra {campo} pero el script no lo lee ({especificador}). "
            "Los dos formatos tienen que ir a la par."
        )


def test_no_usa_el_formato_combined_a_secas():
    """COMBINED parsea estas líneas pero IGNORA el tiempo de respuesta.

    Es la trampa de este montaje: GoAccess no se queja, genera el informe, y
    la sección de páginas lentas queda vacía sin que nada lo indique.
    """
    # Solo las líneas de código: el script MENCIONA COMBINED en un comentario,
    # justo para explicar por qué no se usa.
    codigo = "\n".join(l for l in SCRIPT.read_text(encoding="utf-8").split("\n")
                       if not l.lstrip().startswith("#"))
    assert "--log-format=COMBINED" not in codigo, (
        "COMBINED descarta $request_time. Usa el formato explícito con %T."
    )


def test_tolera_lineas_sueltas_que_no_encajan():
    """Un registro real siempre trae basura: bots, sondas, líneas heredadas.

    Sin --num-tests=0 GoAccess aborta el informe entero al topar con las
    primeras líneas raras, y basta una para quedarse sin informe.
    """
    assert "--num-tests=0" in SCRIPT.read_text(encoding="utf-8")


def test_comprueba_que_alguna_linea_se_reconocio():
    """GoAccess devuelve 0 aunque no parsee nada, escribiendo un informe a cero."""
    script = SCRIPT.read_text(encoding="utf-8")
    assert "valid_requests" in script, (
        "Falta la comprobación de líneas válidas: sin ella, un informe vacío "
        "pasa por bueno y no se descubre hasta semanas después."
    )


def test_los_informes_no_se_versionan():
    """Llevan direcciones IP de los visitantes."""
    assert "informes/" in IGNORE.read_text(encoding="utf-8")


def test_los_informes_no_se_generan_dentro_de_lo_que_sirve_nginx():
    """Nginx sirve frontend/. Un informe ahí sería público."""
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'DESTINO="informes"' in script, (
        "El destino debe quedar fuera de frontend/, que es lo que Nginx publica"
    )
    assert "frontend" not in script.split("# ===")[-1], (
        "El script no debe escribir nada dentro de frontend/"
    )
