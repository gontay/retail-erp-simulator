from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Asset, Depreciation

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/")
def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()


@router.get("/depreciation")
def list_depreciation(db: Session = Depends(get_db)):
    return db.query(Depreciation).all()