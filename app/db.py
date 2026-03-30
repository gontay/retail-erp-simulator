import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
DATABASE_URL = os.environ.get("DBURL")
DB_NAME = os.environ.get("DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")

# =========================================================
# DATABASE URL
# =========================================================
# Example:
# postgresql+psycopg://postgres:password@localhost:5432/retail_erp
DATABASE_URL = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{DATABASE_URL}/{DB_NAME}"


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