"""
Tests del script de copias de seguridad de la base de datos.

Un backup solo vale si se puede restaurar, y eso no se sabe hasta que hace
falta. Estos tests protegen las tres cosas que hacen que ese día funcione:
que las credenciales salgan del .env, que un volcado incompleto se descarte en
vez de guardarse, y que la rotación no se pierda por el camino.
"""
import os
import stat
from pathlib import Path

RAIZ     = Path(__file__).parent.parent
SCRIPT   = RAIZ / "scripts/backup_db.sh"
MAKEFILE = RAIZ / "Makefile"
GITIGNORE = RAIZ / ".gitignore"


def _texto():
    return SCRIPT.read_text(encoding="utf-8")


def test_el_script_existe_y_es_ejecutable():
    assert SCRIPT.is_file()
    assert os.stat(SCRIPT).st_mode & stat.S_IXUSR, "falta permiso de ejecución"


def test_las_credenciales_salen_del_env():
    """Escritas aquí, fallarían en cualquier despliegue con secretos propios."""
    t = _texto()
    assert 'docker/.env' in t
    assert '$MYSQL_USER' in t and '$MYSQL_PASSWORD' in t
    for secreto in ("bdns_pass", "rootpass_bdns"):
        assert secreto not in t, secreto


def test_descarta_un_volcado_incompleto():
    """Que mariadb-dump termine bien no basta: un corte a mitad —disco lleno,
    contenedor parado— deja un fichero truncado con pinta de válido. La marca
    de cierre es lo que distingue uno completo de uno a medias."""
    t = _texto()
    assert "Dump completed" in t
    i = t.index("Dump completed")
    assert "rm -f" in t[i:i + 300], "no se borra el fichero truncado"


def test_borra_el_fichero_si_el_volcado_falla():
    """La redirección crea el fichero ANTES de que se escriba nada: sin esto,
    un fallo dejaría un .sql de 0 bytes con aspecto de backup bueno."""
    t = _texto()
    i = t.index("no se pudo volcar")
    assert "rm -f" in t[max(0, i - 200):i]


def test_hay_rotacion():
    """Sin ella, las copias acaban llenando el disco del servidor."""
    t = _texto()
    assert "-mtime" in t and "-delete" in t
    assert "BACKUP_DIAS" in t, "los días de retención deben ser configurables"


def test_la_retencion_se_lee_despues_del_env():
    """Así se configura UNA vez por entorno, en docker/.env, y vale igual para
    la tarea programada y para un `make backup` a mano.

    Leyéndola antes, habría que pasarla en la línea del cron y un `make backup`
    manual usaría el valor por defecto, borrando copias que se querían
    conservar. Frecuencia y retención van unidas: con copias semanales, 30 días
    dejan solo cuatro."""
    t = _texto()
    # Se busca la ASIGNACIÓN, no cualquier mención: el comentario de cabecera
    # nombra la variable mucho antes y daría un falso negativo.
    asignacion = t.index('DIAS="${BACKUP_DIAS')
    assert asignacion > t.index('. "$ENV_FILE"')


def test_comprueba_que_la_base_de_datos_esta_levantada():
    """Si no, el volcado falla con un error de Docker poco descriptivo."""
    assert "docker ps" in _texto()


def test_make_backup_usa_el_script():
    """Una sola implementación: la misma que ejecuta el servidor."""
    t = MAKEFILE.read_text(encoding="utf-8")
    i = t.index("\nbackup:")
    assert "scripts/backup_db.sh" in t[i:i + 200]


def test_los_volcados_estan_fuera_de_git():
    """Contienen datos reales: usuarios y hashes de contraseña."""
    t = GITIGNORE.read_text(encoding="utf-8")
    assert "backups/" in t or "backup_*.sql" in t
