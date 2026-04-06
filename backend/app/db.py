import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_HOST     = os.environ.get("DB_HOST",     "127.0.0.1")
DB_PORT     = os.environ.get("DB_PORT",     "3307")   # 3307 en local, 3306 dentro de Docker
DB_NAME     = os.environ.get("DB_NAME",     "bdns_dgda")
DB_USER     = os.environ.get("DB_USER",     "bdns_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "bdns_pass")

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
