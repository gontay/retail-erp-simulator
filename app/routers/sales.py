from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import crud, schemas

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/", response_model=list[schemas.SaleRead])
def list_sales(db: Session = Depends(get_db)):
    return crud.get_sales(db)


@router.post("/", response_model=schemas.SaleRead)
def create_sale(payload: schemas.SaleCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_sale(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))