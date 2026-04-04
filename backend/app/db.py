import os
from sqlalchemy import create_engine

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "bdns_dgda")
DB_USER = os.environ.get("DB_USER", "bdns_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "bdns_pass")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
