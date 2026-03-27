from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import crud, schemas

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=list[schemas.InventoryRead])
def list_inventory(db: Session = Depends(get_db)):
    return crud.get_inventory(db)


@router.post("/", response_model=schemas.InventoryRead)
def create_inventory(payload: schemas.InventoryCreate, db: Session = Depends(get_db)):
    return crud.create_inventory(db, payload)