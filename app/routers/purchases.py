from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import crud, schemas

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.get("/", response_model=list[schemas.PurchaseRead])
def list_purchases(db: Session = Depends(get_db)):
    return crud.get_purchases(db)


@router.post("/", response_model=schemas.PurchaseRead)
def create_purchase(payload: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_purchase(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))