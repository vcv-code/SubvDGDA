import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Se aceptan dos juegos de nombres. Dentro de Docker manda DB_*, que es lo que
# pasa docker-compose. Fuera —modo desarrollo con uvicorn en el propio equipo—
# basta con cargar docker/.env, que define MYSQL_*. Sin este segundo juego, el
# backend local se quedaría con los valores por defecto de abajo y no conectaría
# en cuanto la instalación tuviera credenciales propias.
def _cfg(*nombres, defecto):
    for n in nombres:
        v = os.environ.get(n)
        if v:
            return v
    return defecto


DB_HOST     = _cfg("DB_HOST",                     defecto="127.0.0.1")
DB_PORT     = _cfg("DB_PORT",                     defecto="3307")   # 3307 en local, 3306 dentro de Docker
DB_NAME     = _cfg("DB_NAME",     "MYSQL_DATABASE", defecto="bdns_dgda")
DB_USER     = _cfg("DB_USER",     "MYSQL_USER",     defecto="bdns_user")
DB_PASSWORD = _cfg("DB_PASSWORD", "MYSQL_PASSWORD", defecto="bdns_pass")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Opciones de pool, y no son cosméticas: son la causa de la caída del 7-8 de
# septiembre de 2026.
#
# SQLAlchemy guarda las conexiones abiertas para reutilizarlas. MariaDB, por su
# parte, cierra sola las que llevan `wait_timeout` sin usarse —8 horas por
# defecto—. Con la web tranquila de madrugada, al llegar la primera visita del
# día el pool entregaba una conexión que el servidor ya había cerrado, y la
# petición moría con:
#
#     OperationalError (2006) "MySQL server has gone away
#     (ConnectionResetError(104, 'Connection reset by peer'))"
#
#   · pool_pre_ping — antes de entregar una conexión, hace un SELECT 1. Si está
#     muerta, la descarta y abre otra sin que la petición se entere. Es el
#     remedio estándar de este error.
#   · pool_recycle  — además, jubila toda conexión con más de media hora de
#     vida. Muy por debajo de las 8 horas de MariaDB, así que nunca se llega a
#     usar una que el servidor haya cerrado por su cuenta.
#
# El pre_ping cuesta una consulta trivial por petición; el error que evita
# costó dos días de web caída.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Cada petición a la API abre una sesión y la cierra al terminar
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base de la que heredan todos los modelos ORM
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesión de BD por petición y la cierra al acabar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
