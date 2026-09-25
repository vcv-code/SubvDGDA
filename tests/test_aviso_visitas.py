"""
Correo mensual con la evolución de las visitas.

Lo que se protege aquí es una cosa por encima de todo: **que ese correo no
saque datos personales del servidor**. El resumen de visitas lleva direcciones
IP de los visitantes, y adjuntarlo o pegarlo en el cuerpo sería dejarlas en un
buzón sin ninguna necesidad. Las cifras que van salen del histórico, que se
filtra al construirlo.

Y dos más que fallarían en silencio: que un error al enviar no rompa la tarea
programada —un aviso que no sale no puede tumbar lo demás— y que no se le diga
a nadie que tiene informes «sin descargar», porque el servidor no puede saberlo.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
SCRIPT = RAIZ / "scripts/aviso_visitas.py"
MAKEFILE = RAIZ / "Makefile"


def test_el_script_existe():
    assert SCRIPT.exists(), "Falta scripts/aviso_visitas.py"


def test_no_adjunta_el_resumen_de_visitas():
    """El resumen lleva IPs. El correo manda cifras, no ficheros."""
    texto = SCRIPT.read_text(encoding="utf-8")
    assert "add_attachment" not in texto, (
        "Adjunta un fichero: el resumen de visitas lleva direcciones IP")
    assert "set_content" in texto, "No compone un cuerpo de texto"


def test_el_cuerpo_sale_del_historico_y_no_de_los_registros():
    """Los registros crudos tienen IPs; el histórico va filtrado."""
    texto = SCRIPT.read_text(encoding="utf-8")
    assert "historico_visitas" in texto
    assert "logs/nginx" not in texto, (
        "Lee los registros directamente, que es de donde salen las IPs")


def test_un_fallo_al_enviar_no_rompe_la_tarea():
    """Si el SMTP está caído, el cron no puede caerse con él."""
    texto = SCRIPT.read_text(encoding="utf-8")
    bloque = texto[texto.index("def enviar("):texto.index("def main(")]
    assert "except Exception" in bloque, "Un fallo de SMTP tumbaría el cron"
    assert "return False" in bloque


def test_no_dice_cuantos_informes_faltan_por_descargar():
    """El servidor no sabe qué se ha bajado nadie: decirlo sería inventárselo.

    Se mira la SALIDA y no el código, porque en el código la frase aparece en
    el comentario que explica por qué no se usa.
    """
    r = subprocess.run([sys.executable, str(SCRIPT), "--seco"],
                       cwd=RAIZ, capture_output=True, text=True, timeout=60)
    assert "sin descargar" not in r.stdout, (
        "El correo afirma algo que el servidor no puede saber")


def test_el_modo_seco_no_envia_nada():
    """Para poder probar el correo sin mandarlo."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--seco"],
                       cwd=RAIZ, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "Asunto:" in r.stdout
    # Y que lo que sale no lleva IPs.
    ip = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    assert not ip.search(r.stdout), f"El correo llevaría IPs: {ip.findall(r.stdout)[:3]}"


def test_compara_medias_y_avisa_de_ello():
    """Comparar totales entre meses con distinto número de días medidos da
    variaciones inventadas."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--seco"],
                       cwd=RAIZ, capture_output=True, text=True, timeout=60)
    assert "MEDIA DIARIA" in r.stdout, "No advierte de que hay que comparar medias"


def test_make_lo_expone_en_modo_seco():
    mk = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^aviso-visitas:", mk, re.M), "Falta el target"
    assert "--seco" in mk[mk.index("aviso-visitas:"):], (
        "`make aviso-visitas` enviaría el correo de verdad al probarlo")
    phony = re.search(r"\.PHONY:(.*?)(?=\n[^\s\\])", mk, re.S)
    assert phony and "aviso-visitas" in phony.group(1)


def test_traer_informes_se_trae_el_historico_del_servidor():
    """Si solo se alimentara del informe descargado, un mes sin mirar dejaría
    huecos aunque el servidor los tuviera bien guardados."""
    texto = (RAIZ / "scripts/traer_informes.sh").read_text(encoding="utf-8")
    assert "historico.json" in texto, (
        "No se trae el histórico que el servidor mantiene por su cuenta")
