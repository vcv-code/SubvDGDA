"""
Histórico y evolución de visitas.

Lo que se protege aquí son las tres cosas que harían daño en silencio:

  · Que el histórico NO acabe llevando datos personales. Se versiona a
    propósito —es el único sitio donde viven los datos de más de 30 días—, así
    que una IP colada por la cabecera Referer acabaría en el repositorio.

  · Que siga versionándose. Si alguien "limpia" el .gitignore y vuelve a
    excluir `informes/` entero, el fichero deja de subir y nadie se entera
    hasta que hace falta y no está.

  · Que los meses incompletos se marquen. Comparar un mes de 17 días con otro
    de 30 por su total da una caída inventada del 45 %.
"""
import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).parent.parent
HISTORICO = RAIZ / "informes/historico.json"
EXTRACTOR = RAIZ / "scripts/historico_visitas.py"
INFORME = RAIZ / "scripts/evolucion_visitas.py"
IGNORE = RAIZ / ".gitignore"
MAKEFILE = RAIZ / "Makefile"

# IPv4 con o sin corchetes, IPv6 entre corchetes.
_IP = re.compile(r"\[?(?:\d{1,3}\.){3}\d{1,3}\]?|\[[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4}){2,}\]")


def test_los_scripts_existen():
    assert EXTRACTOR.exists(), "Falta scripts/historico_visitas.py"
    assert INFORME.exists(), "Falta scripts/evolucion_visitas.py"


def test_el_historico_no_guarda_direcciones_ip():
    """Se versiona: una IP aquí acaba publicada en el repositorio.

    Llegan por el Referer cuando alguien enlaza desde una URL con IP en vez de
    dominio, así que no basta con confiar en que no aparezcan.
    """
    if not HISTORICO.exists():
        return  # todavía sin sembrar; el extractor lo crea
    texto = HISTORICO.read_text(encoding="utf-8")
    # Las fechas (2026-08-15) no son IPs; se buscan solo patrones con puntos.
    assert not _IP.search(texto), (
        f"El histórico contiene direcciones IP: {_IP.findall(texto)[:3]}")


def test_el_historico_no_guarda_cadenas_de_ataque():
    """Por el Referer llegan sondeos tipo ${jndi:ldap:…} buscando Log4Shell."""
    if not HISTORICO.exists():
        return
    texto = HISTORICO.read_text(encoding="utf-8").lower()
    for basura in ("jndi:", "${", "<script"):
        assert basura not in texto, f"El histórico contiene «{basura}»"


def test_el_extractor_filtra_esas_dos_cosas():
    """Aunque hoy el fichero esté limpio, el filtro tiene que seguir ahí."""
    texto = EXTRACTOR.read_text(encoding="utf-8")
    assert "_BASURA" in texto and "jndi" in texto, (
        "Se ha perdido el filtro de IPs y cadenas de ataque")


def test_el_historico_si_se_versiona():
    """Es el único sitio donde viven los datos de más de 30 días.

    `informes/` va ignorado por las IPs de los informes HTML, pero este fichero
    lleva su excepción. Ojo: la carpeta se ignora como `informes/*` y no como
    `informes/`, porque git no puede rescatar un fichero cuyo directorio padre
    está excluido.
    """
    reglas = IGNORE.read_text(encoding="utf-8")
    assert "!informes/historico.json" in reglas, "Falta la excepción"
    assert "informes/*" in reglas, (
        "La carpeta se ignora como `informes/`, y así la excepción no funciona")
    r = subprocess.run(["git", "check-ignore", "-q", "informes/historico.json"],
                       cwd=RAIZ, capture_output=True)
    assert r.returncode != 0, "git sigue ignorando el histórico"


def test_los_informes_con_ip_siguen_fuera_del_repositorio():
    """La excepción no puede haber abierto la puerta a los HTML."""
    r = subprocess.run(["git", "check-ignore", "-q",
                        "informes/servidor/resumen-2026-09-25-30dias.html"],
                       cwd=RAIZ, capture_output=True)
    assert r.returncode == 0, "Los informes HTML han dejado de estar ignorados"


def test_los_meses_incompletos_se_marcan():
    """Comparar por totales un mes de 17 días con otro de 30 inventa una caída."""
    texto = INFORME.read_text(encoding="utf-8")
    assert "completo" in texto and "media" in texto, (
        "No distingue meses completos de parciales")
    # En SVG la marca es un patrón rayado, no una clase CSS.
    assert "rayas" in texto and 'url(#rayas)' in texto, (
        "No hay marca visual para los meses parciales")
    assert "de {m[\"esperados\"]} días" in texto or "esperados" in texto, (
        "No se dice cuántos días tiene un mes parcial")


def test_make_expone_el_informe():
    mk = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^evolucion:", mk, re.M), "Falta el target `evolucion`"
    phony = re.search(r"\.PHONY:(.*?)(?=\n[^\s\\])", mk, re.S)
    assert phony and "evolucion" in phony.group(1), "`evolucion` no está en .PHONY"


def test_el_historico_se_alimenta_al_traer_informes():
    """Si hay que acordarse de ejecutarlo, no se ejecuta: los días se pierden
    a los 30 y no se recuperan."""
    texto = (RAIZ / "scripts/traer_informes.sh").read_text(encoding="utf-8")
    assert "historico_visitas.py" in texto, (
        "traer_informes.sh no alimenta el histórico")


def test_el_informe_se_puede_guardar_como_pdf():
    """El botón de imprimir tiene que desaparecer AL imprimir.

    Sin la regla @media print sale en el PDF un botón verde que nadie va a
    poder pulsar, que es de esos detalles que delatan una página sin repasar.
    """
    texto = INFORME.read_text(encoding="utf-8")
    assert "window.print()" in texto, "No hay botón de guardar como PDF"
    assert "@media print" in texto and "display:none" in texto, (
        "El botón de imprimir saldría dentro del propio PDF")


def test_se_abre_solo_pero_se_puede_evitar():
    """En WSL hay que traducir la ruta: el navegador es de Windows y no
    entiende las rutas de Linux."""
    texto = INFORME.read_text(encoding="utf-8")
    assert "wslpath" in texto, "No funcionaría en WSL, que es donde se usa"
    assert 'os.environ.get("ABRIR"' in texto, (
        "Sin ABRIR=no no se puede generar el informe sin abrir ventana, "
        "que es lo que hace falta si algún día lo lanza una tarea programada")


def test_la_grafica_va_en_svg_para_que_se_imprima():
    """Los navegadores NO imprimen fondos de color por defecto.

    Con barras hechas de `div` + `background`, el PDF salía con los números y
    las etiquetas pero sin barras. El `fill` de un SVG sí se imprime, que es
    como lo hace resumen_visitas.py y por eso aquel imprimía bien.
    """
    texto = INFORME.read_text(encoding="utf-8")
    assert "<svg" in texto and "<rect" in texto, "La gráfica no va en SVG"
    assert "barra__caja" not in texto, (
        "Quedan restos de las barras con fondo CSS, que no se imprimen")


def test_se_abre_en_chrome_y_se_puede_cambiar():
    """El navegador predeterminado de la máquina es Edge, y los informes se
    revisan en Chrome."""
    for script in (INFORME, RAIZ / "scripts/traer_informes.sh"):
        texto = script.read_text(encoding="utf-8")
        assert "chrome.exe" in texto.lower(), f"{script.name} no busca Chrome"
        assert "NAVEGADOR" in texto, (
            f"{script.name} no deja elegir otro navegador")
        assert "explorer.exe" in texto, (
            f"{script.name} se queda sin respaldo si Chrome no está instalado")


def test_busca_los_informes_en_las_dos_carpetas():
    """El mismo script corre en dos sitios con la estructura invertida.

    En el servidor los informes se generan en `informes/` a secas y no existe
    `informes/servidor/`; en la máquina de trabajo es al revés. Mirar solo una
    hacía que la tarea semanal del servidor no encontrara nada y saliera con
    error, cosa que se vio ejecutándola allí después de desplegar.
    """
    texto = EXTRACTOR.read_text(encoding="utf-8")
    assert 'RAIZ / "informes"' in texto and 'RAIZ / "informes/servidor"' in texto, (
        "No mira las dos carpetas: en uno de los dos sitios no encontrará nada")


def test_la_ruta_del_historico_es_configurable():
    """En el servidor NO puede escribir sobre el fichero versionado.

    `informes/historico.json` es el único de esa carpeta que git rastrea, y
    allí lo modificaría una tarea semanal: un fichero rastreado que cambia solo
    en el servidor aborta el `git pull` del siguiente despliegue con «local
    changes would be overwritten». Por eso allí se apunta con HISTORICO_FILE a
    otro nombre, que queda ignorado.
    """
    texto = EXTRACTOR.read_text(encoding="utf-8")
    assert "HISTORICO_FILE" in texto, "La ruta no se puede cambiar"
    manual = (RAIZ / "manuales/manual-despliegue.md").read_text(encoding="utf-8")
    assert "HISTORICO_FILE=" in manual, (
        "El crontab documentado no la define: el servidor escribiría sobre el "
        "fichero versionado")
    r = subprocess.run(["git", "check-ignore", "-q",
                        "informes/historico-servidor.json"],
                       cwd=RAIZ, capture_output=True)
    assert r.returncode == 0, "El histórico del servidor acabaría en el repositorio"


def test_el_cron_recoge_la_salida_de_las_dos_ordenes():
    """En `A && B >> fichero` la redirección se aplica solo a B.

    Si el resumen fallara, su error no llegaría al log y este diría únicamente
    que el histórico no encontró informes — culpando a la orden equivocada.
    """
    manual = (RAIZ / "manuales/manual-despliegue.md").read_text(encoding="utf-8")
    linea = next(l for l in manual.splitlines()
                 if "resumen_visitas.py --dias" in l and l.startswith("0 5"))
    assert "{" in linea and "}" in linea, (
        "Las dos órdenes no van agrupadas: la salida de la primera se pierde")


def test_el_historico_tiene_la_forma_esperada():
    if not HISTORICO.exists():
        return
    d = json.loads(HISTORICO.read_text(encoding="utf-8"))
    assert set(d) >= {"dias", "periodos"}
    for dia, n in d["dias"].items():
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", dia), f"fecha rara: {dia}"
        assert isinstance(n, int) and n >= 0
