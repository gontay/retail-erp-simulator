from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..utils.accounting import post_journal_entry

router = APIRouter(prefix="/inventory", tags=["Inventory"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def inventory_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="inventory.html",
        context= {
        "request": request,
        "message": None,
        "error": None
    })


@router.post("/new")
def submit_inventory(
    request: Request,
    sku: str = Form(...),
    product_name: str = Form(...),
    category: str = Form(...),
    unit_price: float = Form(...),
    unit_cost: float = Form(...),
    quantity_on_hand: float = Form(...),
    db: Session = Depends(get_db),
):
    try:
        existing = db.query(models.Inventory).filter(models.Inventory.sku == sku).first()
        if existing:
            raise ValueError("SKU already exists.")

        qty = Decimal(str(quantity_on_hand))
        cost = Decimal(str(unit_cost))
        price = Decimal(str(unit_price))

        item = models.Inventory(
            sku=sku,
            product_name=product_name,
            category=category,
            unit_price=price,
            unit_cost=cost,
            quantity_on_hand=qty
        )
        db.add(item)
        db.flush()

        opening_value = qty * cost

        if qty > 0:
            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "1200", "Inventory", debit=opening_value)
            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "3000", "Opening Equity Adjustment", credit=opening_value)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="inventory.html",
            context= {
            "request": request,
            "message": f"Inventory item '{product_name}' created successfully.",
            "error": None
        })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="inventory.html",
            context= {
            "request": request,
            "message": None,
            "error": str(e)
        })