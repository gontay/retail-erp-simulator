import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
# =========================================================
# DATABASE URL
# =========================================================
# Example:
# postgresql+psycopg://postgres:password@localhost:5432/retail_erp

#use this for cloud based DB example: Supabase
DATABASE_URL = os.environ.get("DB_URL")

#use this for local PostgresDB 
#DBURL = os.environ.get("DBURL")
#DB_NAME = os.environ.get("DBNAME")
#PG_USER = os.environ.get("PG_USER")
#PG_PASSWORD = os.environ.get("PG_PASSWORD")
#DATABASE_URL = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{DBURL}/{DB_NAME}"


# =========================================================
# ENGINE
# =========================================================
engine = create_engine(
    DATABASE_URL,
    echo=True,   # set to False later if logs get noisy
    future=True
)

# =========================================================
# SESSION
# =========================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =========================================================
# BASE
# =========================================================
Base = declarative_base()

# =========================================================
# DEPENDENCY
# =========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()