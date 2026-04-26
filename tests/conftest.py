import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import Base, get_db
import backend.app.models  # necesario para que SQLAlchemy registre las tablas antes de create_all

# StaticPool obliga a que todas las conexiones compartan la misma BD en memoria.
# Sin esto, create_all crea las tablas en una conexión y los tests usan otra distinta.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db():
    """Versión de get_db que apunta a SQLite en vez de MariaDB."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI sustituye get_db por override_get_db en todos los tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Crea las tablas antes del test y las borra al terminar."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(client):
    """Sesión de BD para insertar datos de prueba en los tests."""
    session = TestingSessionLocal()
    yield session
    session.close()
