from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..utils.accounting import post_journal_entry

router = APIRouter(prefix="/purchases", tags=["Purchases"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def purchase_form(request: Request, db: Session = Depends(get_db)):
    suppliers = db.query(models.Supplier).all()
    inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

    return templates.TemplateResponse(
        name="purchases.html",
        request=request,
        context= {
        "request": request,
        "suppliers": suppliers,
        "inventory_items": inventory_items,
        "message": None,
        "error": None
    })


@router.post("/new")
def submit_purchase(
    request: Request,
    supplier_id: int = Form(...),
    purchase_date: str = Form(...),
    payment_method: str = Form(...),
    inventory_id: int = Form(...),
    quantity: float = Form(...),
    unit_cost: float = Form(...),
    db: Session = Depends(get_db),
):
    suppliers = db.query(models.Supplier).all()
    inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

    try:
        purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d").date()
        qty = Decimal(str(quantity))
        cost = Decimal(str(unit_cost))
        total_amount = qty * cost

        inventory = db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
        if not inventory:
            raise ValueError("Inventory item not found.")

        purchase = models.Purchases(
            supplier_id=supplier_id,
            purchase_date=purchase_dt,
            total_amount=total_amount,
            payment_method=payment_method,
            status="Received"
        )
        db.add(purchase)
        db.flush()

        db.add(models.PurchaseItem(
            purchase_id=purchase.id,
            inventory_id=inventory.id,
            quantity=qty,
            unit_cost=cost,
            line_total=total_amount
        ))

        inventory.quantity_on_hand = Decimal(str(inventory.quantity_on_hand)) + qty
        inventory.unit_cost = cost

        post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1200", "Inventory", debit=total_amount)

        if payment_method.lower() == "credit":
            post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "2100", "Accounts Payable", credit=total_amount)
            db.add(models.AccountsPayable(
                supplier_id=supplier_id,
                purchase_id=purchase.id,
                amount_due=total_amount,
                due_date=purchase_dt,
                status="Open"
            ))
        else:
            post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1000", "Cash / Treasury", credit=total_amount)

        db.commit()

        return templates.TemplateResponse(        
            name="purchases.html",
            request=request,
            context={
            "request": request,
            "suppliers": suppliers,
            "inventory_items": inventory_items,
            "message": f"Purchase #{purchase.id} created successfully.",
            "error": None
        })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            name="purchases.html",
            request=request,
            context={
            "request": request,
            "suppliers": suppliers,
            "inventory_items": inventory_items,
            "message": None,
            "error": str(e)
        })