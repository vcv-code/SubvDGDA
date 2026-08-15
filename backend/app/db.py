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

engine = create_engine(DATABASE_URL)

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
