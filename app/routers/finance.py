from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import AccountsReceivable, AccountsPayable, UniversalJournal, Treasury, CashFloat

router = APIRouter(prefix="/finance", tags=["Finance"])


@router.get("/ar")
def list_ar(db: Session = Depends(get_db)):
    return db.query(AccountsReceivable).all()


@router.get("/ap")
def list_ap(db: Session = Depends(get_db)):
    return db.query(AccountsPayable).all()


@router.get("/journal")
def list_journal(db: Session = Depends(get_db)):
    return db.query(UniversalJournal).all()


@router.get("/treasury")
def list_treasury(db: Session = Depends(get_db)):
    return db.query(Treasury).all()


@router.get("/cash-float")
def list_cash_float(db: Session = Depends(get_db)):
    return db.query(CashFloat).all()