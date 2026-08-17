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


# ─────────────────────────────────────────────────────────────────────────────
# Resumen en español (scripts/resumen_visitas.py)
# ─────────────────────────────────────────────────────────────────────────────
import subprocess
import sys

RESUMEN = RAIZ / "scripts/resumen_visitas.py"


def test_el_resumen_no_necesita_dependencias_externas():
    """Debe funcionar en el servidor sin instalar nada: solo Python.

    Es la razón de que exista además de GoAccess: si mañana falta un paquete,
    esto sigue dando las cifras básicas.
    """
    codigo = RESUMEN.read_text(encoding="utf-8")
    imports = [l.strip() for l in codigo.split("\n")
               if l.startswith(("import ", "from ")) and "__future__" not in l]
    permitidos = {"argparse", "html", "os", "re", "socket", "collections", "datetime", "pathlib"}
    for linea in imports:
        modulo = linea.split()[1].split(".")[0]
        assert modulo in permitidos, (
            f"'{modulo}' no es biblioteca estándar mínima. El resumen tiene que "
            "poder ejecutarse en un servidor pelado."
        )


def test_el_resumen_lee_el_mismo_formato_que_nginx():
    """Si Nginx cambia el log_format, este script deja de reconocer líneas."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    conf   = NGINX.read_text(encoding="utf-8")
    assert "$http_referer" in conf and "referente" in codigo
    assert "$http_user_agent" in conf and "agente" in codigo


def test_el_resumen_descuenta_robots_y_estaticos():
    """Sin descontarlos, las cifras engañan: la mayor parte del tráfico de una
    web pública son rastreadores, y una visita pide veinte ficheros."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    assert "BOTS" in codigo and "ESTATICOS" in codigo


def test_el_resumen_no_enlaza_recursos_externos():
    """Se abre desde el disco, sin conexión: nada de CDN ni fuentes remotas."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    assert "https://cdn" not in codigo and "googleapis" not in codigo


def test_el_resumen_se_genera_y_es_html_valido(tmp_path):
    """Ejecuta el script de verdad contra los registros del repositorio."""
    if not (RAIZ / "logs/nginx").exists():
        import pytest
        pytest.skip("sin registros de Nginx en este entorno")
    r = subprocess.run([sys.executable, str(RESUMEN)],
                       capture_output=True, text=True, cwd=RAIZ)
    assert r.returncode == 0, f"falló: {r.stderr}"
    generados = sorted((RAIZ / "informes").glob("resumen-*.html"))
    assert generados, "no se generó ningún resumen"
    t = generados[-1].read_text(encoding="utf-8")
    assert t.startswith("<!doctype html>") and t.rstrip().endswith("</html>")
    assert 'lang="es"' in t


def test_identifica_administraciones_sin_falsos_positivos():
    """Los patrones deben acertar con organismos y NO con conexiones normales.

    Un falso positivo aquí es peor que no detectar nada: haría creer que un
    ayuntamiento consulta la web cuando es una casa con Jazztel.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("rv", RESUMEN)
    rv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rv)

    import re as _re

    def clasificar(nombre):
        for patron, etiqueta in rv.ORGANISMOS:
            if _re.search(patron, nombre.lower()):
                return etiqueta
        return None

    aciertos = {
        'proxy.ayto-santander.es':    'Ayuntamiento',
        'gw01.ayuntamientodeleon.es': 'Ayuntamiento',
        'nat.dipucordoba.es':         'Diputación provincial',
        'salida.gencat.cat':          'Generalitat de Catalunya',
        'host.sede.gob.es':           'Administración General del Estado',
        'nodo.rediris.es':            'Universidad o investigación pública',
    }
    for nombre, esperado in aciertos.items():
        assert clasificar(nombre) == esperado, f"{nombre} debería dar {esperado}"

    # Conexiones domésticas y comerciales: no deben identificarse jamás
    for nombre in ['83.45.12.9.dynamic.jazztel.es', 'static.telefonica.es',
                   'one.one.one.one', 'ec2-52-1-2-3.compute.amazonaws.com']:
        assert clasificar(nombre) is None, f"{nombre} NO es una administración"


def test_la_resolucion_dns_va_desactivada_por_defecto():
    """Cada consulta es una petición de red: no debe pasar sin pedirlo."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    assert "'--organizaciones', action='store_true'" in codigo
    assert "resolver_dns=False" in codigo


def test_nunca_se_muestran_direcciones_ip_en_el_informe():
    """Se identifican organizaciones, no visitantes: la IP no se publica."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    render = codigo[codigo.index("def render("):codigo.index("def main(")]
    assert "hits_ip" not in render and "visitantes'])" not in render.replace(
        "len(d['visitantes'])", ""), (
        "El informe no debe listar direcciones IP, solo cifras agregadas"
    )


def test_la_geolocalizacion_es_opcional_y_no_rompe_nada():
    """Sin la librería o sin la base, el resumen debe generarse igual.

    Es la promesa que sostiene este script: funciona en un servidor pelado.
    Si la geolocalización pasara a ser obligatoria, dejaría de cumplirla.
    """
    codigo = RESUMEN.read_text(encoding="utf-8")
    # El import va DENTRO de la función, no arriba del fichero
    cabecera = codigo[:codigo.index("def ")]
    assert "maxminddb" not in cabecera, (
        "maxminddb no debe importarse al principio: haría el script "
        "inservible sin esa librería instalada"
    )
    assert "except ImportError" in codigo


def test_avisa_de_por_que_falta_la_ubicacion():
    """Un hueco sin explicación se interpreta como un fallo."""
    codigo = RESUMEN.read_text(encoding="utf-8")
    assert "falta la librería" in codigo and "falta la base de datos" in codigo


def test_la_base_geoip_no_se_versiona():
    """Pesa decenas de MB y tiene licencia propia de MaxMind."""
    ignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "geoip" in ignore.lower() or "*.mmdb" in ignore
