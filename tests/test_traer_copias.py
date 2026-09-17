"""
Traer las copias de seguridad del servidor (scripts/traer_copias.sh).

Lo que se protege aquí no es que el `scp` funcione —eso se comprueba
ejecutándolo—, sino las tres cosas que fallarían en silencio:

  · Que las copias del servidor NO acaben mezcladas con los volcados locales.
    Restaurar la equivocada es de los errores más caros que se pueden cometer
    aquí, y un nombre de fichero casi idéntico lo pone fácil.

  · Que no acaben versionadas. Llevan las cuentas de usuario con sus hashes de
    contraseña: basta con dejarlas en una carpeta que git no ignore.

  · Que se compruebe la marca de cierre del volcado. Un `mysqldump` cortado a
    medias restaura una base de datos incompleta, y eso es PEOR que no tener
    copia, porque parece que ha funcionado.
"""
import re
import stat
from pathlib import Path

RAIZ     = Path(__file__).parent.parent
SCRIPT   = RAIZ / "scripts/traer_copias.sh"
MAKEFILE = RAIZ / "Makefile"
IGNORE   = RAIZ / ".gitignore"


def test_el_script_existe_y_es_ejecutable():
    assert SCRIPT.exists(), "Falta scripts/traer_copias.sh"
    assert SCRIPT.stat().st_mode & stat.S_IXUSR, "No tiene permiso de ejecución"


def test_las_copias_del_servidor_van_a_su_propia_carpeta():
    """Separadas de backups/, como los informes del servidor de los locales."""
    texto = SCRIPT.read_text(encoding="utf-8")
    m = re.search(r'^DESTINO="([^"]+)"', texto, re.M)
    assert m, "El script no declara DESTINO"
    assert m.group(1) == "backups/servidor", (
        f"Las copias del servidor irían a {m.group(1)}, mezcladas con las locales"
    )


def test_el_destino_no_se_versiona():
    """Contienen usuarios y hashes de contraseña."""
    ignore = IGNORE.read_text(encoding="utf-8").splitlines()
    assert any(l.strip() in ("backups/", "backups/*") for l in ignore), (
        "backups/ no está en .gitignore: las copias acabarían en el repositorio"
    )


def test_comprueba_que_el_volcado_no_venga_truncado():
    """Un volcado cortado restaura una BD incompleta sin dar ningún error.

    Es la misma comprobación que hace `make restore` antes de tocar nada.
    """
    texto = SCRIPT.read_text(encoding="utf-8")
    assert "Dump completed" in texto, (
        "No verifica la marca de cierre de mysqldump"
    )


def test_reutiliza_una_sola_conexion_ssh():
    """Sin multiplexar, cada scp abre su propia sesión y la clave vuelve a pedir
    la contraseña: traerse seis copias eran SIETE peticiones seguidas.

    Se detectó probándolo de verdad contra el servidor, no leyendo el script.
    """
    texto = SCRIPT.read_text(encoding="utf-8")
    assert "ControlMaster" in texto and "ControlPath" in texto, (
        "No multiplexa la conexión: volvería a pedir la contraseña por fichero"
    )
    assert "trap" in texto, (
        "El socket de control se quedaría abierto si el script aborta"
    )


def test_el_makefile_lo_expone_y_lo_declara_phony():
    """Sin estar en .PHONY, `make copias` no se ejecutaría si existiera un
    fichero o carpeta llamado «copias»."""
    mk = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^copias:", mk, re.M), "Falta el target `copias`"
    phony = re.search(r"\.PHONY:(.*?)(?=\n[^\s\\])", mk, re.S)
    assert phony and "copias" in phony.group(1), "`copias` no está en .PHONY"
