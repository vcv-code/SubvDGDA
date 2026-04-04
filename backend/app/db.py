from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://bdns_user:bdns_pass@db:3306/bdns_dgda"

engine = create_engine(DATABASE_URL)