"""
Tests del despliegue con secretos propios.

Todos nacen de fallos reales detectados al desplegar en un servidor: en local
no se manifestaban porque el .env de desarrollo usaba justo los mismos valores
que estaban escritos en el código, así que los dos caminos daban lo mismo y
nadie notaba que uno estaba mal.
"""
import importlib
import os
import re
from pathlib import Path
from unittest.mock import patch

RAIZ      = Path(__file__).parent.parent
MAKEFILE  = RAIZ / "Makefile"
INSTALL   = RAIZ / "install.sh"
COMPOSE   = RAIZ / "docker/docker-compose.yml"


# ── Credenciales de la base de datos ────────────────────────────────────────

def _recargar_cargador(entorno):
    """Reimporta cargar_dataset con el entorno indicado y lo deja como estaba."""
    import scripts.data_processing.cargar_dataset as cd
    try:
        with patch.dict(os.environ, entorno, clear=True):
            m = importlib.reload(cd)
            return {"user": m.DB_USER, "password": m.DB_PASSWORD, "name": m.DB_NAME}
    finally:
        importlib.reload(cd)


def test_el_cargador_acepta_los_nombres_mysql():
    """docker/.env define MYSQL_*, no DB_*: sin esto usaba la contraseña del código."""
    v = _recargar_cargador({
        "MYSQL_USER": "usuario_real",
        "MYSQL_PASSWORD": "secreto_real",
        "MYSQL_DATABASE": "bd_real",
    })
    assert v == {"user": "usuario_real", "password": "secreto_real", "name": "bd_real"}


def test_los_nombres_db_tienen_prioridad():
    """Dentro de los contenedores manda DB_*, que es lo que pasa compose."""
    v = _recargar_cargador({"DB_PASSWORD": "de_docker", "MYSQL_PASSWORD": "de_env"})
    assert v["password"] == "de_docker"


def test_una_variable_vacia_no_tapa_a_la_siguiente():
    """compose propaga las variables no definidas como cadena vacía."""
    v = _recargar_cargador({"DB_PASSWORD": "", "MYSQL_PASSWORD": "de_env"})
    assert v["password"] == "de_env"


def test_el_backend_tambien_acepta_los_nombres_mysql():
    """Modo desarrollo: uvicorn corre fuera de Docker y solo hay MYSQL_* tras
    cargar docker/.env. Sin esto, el backend local no conectaría en cuanto la
    instalación tuviera credenciales propias."""
    import backend.app.db as db
    try:
        with patch.dict(os.environ, {"MYSQL_USER": "u", "MYSQL_PASSWORD": "p",
                                     "MYSQL_DATABASE": "bd"}, clear=True):
            m = importlib.reload(db)
            assert m.DB_USER == "u" and m.DB_PASSWORD == "p" and m.DB_NAME == "bd"
    finally:
        importlib.reload(db)


# ── Nada de credenciales escritas en ficheros versionados ───────────────────

def test_el_makefile_no_lleva_credenciales_escritas():
    """Estaban en backup, restore y shell-db: los tres fallaban en el servidor."""
    texto = MAKEFILE.read_text(encoding="utf-8")
    for secreto in ("bdns_pass", "rootpass_bdns"):
        assert secreto not in texto, secreto


def test_las_recetas_de_bd_cargan_el_env():
    """Cada receta que toca la BD tiene que sacar las credenciales de
    docker/.env, o bien cargándolo en su propio shell con $(ENV_BD), o bien
    delegando en un script que lo hace por su cuenta."""
    texto = MAKEFILE.read_text(encoding="utf-8")
    SCRIPTS_QUE_CARGAN_ENV = ("scripts/backup_db.sh",)
    for receta in ("backup:", "restore:", "shell-db:", "cargar:"):
        i = texto.index("\n" + receta)
        bloque = texto[i:texto.index("\n\n", i)]
        directo = "$(ENV_BD)" in bloque
        delegado = any(s in bloque for s in SCRIPTS_QUE_CARGAN_ENV)
        assert directo or delegado, receta


def test_los_scripts_delegados_cargan_el_env_de_verdad():
    """Contrapeso del test anterior: si una receta delega, hay que comprobar
    que el script al que delega carga el .env. Si no, el test de arriba daría
    por buena una receta sin credenciales."""
    for ruta in ("scripts/backup_db.sh",):
        t = (RAIZ / ruta).read_text(encoding="utf-8")
        assert "docker/.env" in t, ruta
        assert ". \"$ENV_FILE\"" in t or ". docker/.env" in t, ruta


def test_install_no_escribe_contrasenas_fijas_de_bd():
    """El .env generado debe llevar credenciales propias de cada instalación."""
    texto = INSTALL.read_text(encoding="utf-8")
    assert "MYSQL_ROOT_PASSWORD=rootpass_bdns" not in texto
    assert "MYSQL_PASSWORD=bdns_pass" not in texto
    assert "openssl rand" in texto


# ── Puertos ─────────────────────────────────────────────────────────────────

def _puertos_publicados():
    texto = COMPOSE.read_text(encoding="utf-8")
    return re.findall(r'^\s+- "((?:127\.0\.0\.1:)?\d+:\d+)"', texto, re.MULTILINE)


def test_los_puertos_de_administracion_solo_escuchan_en_local():
    """ufw NO los protege: Docker escribe sus reglas por delante de las suyas.

    Mailpit es el peligroso: accesible desde fuera, cualquiera pide una
    recuperación de contraseña, lee el enlace y se hace administrador.
    """
    for puerto in ("3307:3306", "1025:1025", "8025:8025", "8080:8080"):
        assert f"127.0.0.1:{puerto}" in _puertos_publicados(), puerto


def test_la_web_si_es_publica():
    """80 y 443 tienen que seguir escuchando en todas las interfaces."""
    publicados = _puertos_publicados()
    assert "80:80" in publicados
    assert "443:443" in publicados
