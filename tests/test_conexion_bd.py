"""
Salud del pool de conexiones a MariaDB.

Es la causa de la caída del 7-8 de septiembre de 2026. SQLAlchemy guarda las
conexiones abiertas para reutilizarlas; MariaDB cierra sola las que llevan
`wait_timeout` sin usarse —8 horas por defecto—. Con la web tranquila de
madrugada, la primera visita del día recibía una conexión que el servidor ya
había cerrado:

    OperationalError (2006) "MySQL server has gone away
    (ConnectionResetError(104, 'Connection reset by peer'))"

Reproducido matando las conexiones desde MariaDB: sin estas opciones la
siguiente petición devuelve 500; con ellas, 200.
"""
import re
from pathlib import Path

FUENTE = Path("backend/app/db.py").read_text(encoding="utf-8")


def _argumentos_del_motor():
    i = FUENTE.index("engine = create_engine(")
    return FUENTE[i:FUENTE.index(")", i) + 1]


def test_comprueba_la_conexion_antes_de_usarla():
    """`pool_pre_ping` hace un SELECT 1 antes de entregar una conexión del
    pool: si está muerta la descarta y abre otra sin que la petición se entere.
    Es el remedio estándar de «MySQL server has gone away»."""
    assert "pool_pre_ping=True" in _argumentos_del_motor()


def test_jubila_las_conexiones_antes_de_que_mariadb_las_cierre():
    """`pool_recycle` tiene que quedar holgadamente por debajo del
    `wait_timeout` del servidor (28.800 s por defecto). Si lo igualara o
    superara, volveríamos a entregar conexiones ya cerradas."""
    m = re.search(r"pool_recycle\s*=\s*(\d+)", _argumentos_del_motor())
    assert m, "falta pool_recycle"
    assert 0 < int(m.group(1)) < 28800, f"pool_recycle={m.group(1)} no protege"


def test_el_motor_no_se_crea_sin_opciones():
    """Así estaba cuando ocurrió la caída: `create_engine(DATABASE_URL)` a
    secas, sin comprobar ni renovar nada."""
    assert not re.search(r"create_engine\(\s*DATABASE_URL\s*\)", FUENTE)
