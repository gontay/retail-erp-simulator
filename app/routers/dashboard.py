from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from ..models import Sales, Purchases, Inventory, AccountsReceivable, AccountsPayable

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_sales = db.query(func.coalesce(func.sum(Sales.net_amount), 0)).scalar()
    total_purchases = db.query(func.coalesce(func.sum(Purchases.net_amount), 0)).scalar()
    inventory_count = db.query(func.count(Inventory.id)).scalar()
    ar_total = db.query(func.coalesce(func.sum(AccountsReceivable.balance), 0)).scalar()
    ap_total = db.query(func.coalesce(func.sum(AccountsPayable.balance), 0)).scalar()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_sales": total_sales,
            "total_purchases": total_purchases,
            "inventory_count": inventory_count,
            "ar_total": ar_total,
            "ap_total": ap_total,
        }
    )