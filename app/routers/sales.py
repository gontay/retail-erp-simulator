from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..utils.accounting import post_journal_entry

router = APIRouter(prefix="/sales", tags=["Sales"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def sales_form(request: Request, db: Session = Depends(get_db)):
    customers = db.query(models.Customer).all()
    inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

    return templates.TemplateResponse(
        request=request,
        name="sales.html",
        context= {
        "request": request,
        "customers": customers,
        "inventory_items": inventory_items,
        "message": None,
        "error": None
    })


@router.post("/new")
def submit_sale(
    request: Request,
    customer_id: int = Form(...),
    sale_date: str = Form(...),
    payment_method: str = Form(...),
    inventory_id: int = Form(...),
    quantity: float = Form(...),
    unit_price: float = Form(...),
    db: Session = Depends(get_db),
):
    customers = db.query(models.Customer).all()
    inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

    try:
        sale_dt = datetime.strptime(sale_date, "%Y-%m-%d").date()
        qty = Decimal(str(quantity))
        price = Decimal(str(unit_price))

        inventory = db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
        if not inventory:
            raise ValueError("Inventory item not found.")

        if Decimal(str(inventory.quantity_on_hand)) < qty:
            raise ValueError("Insufficient stock.")

        unit_cost = Decimal(str(inventory.unit_cost or 0))
        sales_total = qty * price
        cogs_total = qty * unit_cost

        sale = models.Sales(
            customer_id=customer_id,
            sale_date=sale_dt,
            total_amount=sales_total,
            payment_method=payment_method,
            status="Completed"
        )
        db.add(sale)
        db.flush()

        db.add(models.SaleItem(
            sale_id=sale.id,
            inventory_id=inventory.id,
            quantity=qty,
            unit_price=price,
            line_total=sales_total
        ))

        inventory.quantity_on_hand = Decimal(str(inventory.quantity_on_hand)) - qty

        if payment_method.lower() == "credit":
            post_journal_entry(db, sale_dt, "SALE", sale.id, "1100", "Accounts Receivable", debit=sales_total)
            db.add(models.AccountsReceivable(
                customer_id=customer_id,
                sale_id=sale.id,
                amount_due=sales_total,
                due_date=sale_dt,
                status="Open"
            ))
        else:
            post_journal_entry(db, sale_dt, "SALE", sale.id, "1000", "Cash / Treasury", debit=sales_total)

        post_journal_entry(db, sale_dt, "SALE", sale.id, "4000", "Sales Revenue", credit=sales_total)
        post_journal_entry(db, sale_dt, "SALE", sale.id, "5000", "Cost of Goods Sold", debit=cogs_total)
        post_journal_entry(db, sale_dt, "SALE", sale.id, "1200", "Inventory", credit=cogs_total)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="sales.html",
            context= {
            "request": request,
            "customers": customers,
            "inventory_items": inventory_items,
            "message": f"Sale #{sale.id} created successfully.",
            "error": None
        })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="sales.html",
            context={
            "request": request,
            "customers": customers,
            "inventory_items": inventory_items,
            "message": None,
            "error": str(e)
        })