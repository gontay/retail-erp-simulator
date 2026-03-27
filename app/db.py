from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# env_path = Path('.')/'.env'
#dotenv_path=env_path)
load_dotenv()

DATABASE_URL = os.environ.get("DBURL")
DB_NAME = os.environ.get("DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")

engine = create_engine(
    f'postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{DATABASE_URL}/{DB_NAME}',
    echo=True,
    future=True,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()