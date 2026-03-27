from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Sales, Delivery, DeliveryItem, SaleItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def delivery_page(request: Request, db: Session = Depends(get_db)):
    sales = db.query(Sales).all()
    deliveries = db.query(Delivery).order_by(Delivery.delivery_id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="delivery.html",
        context={
        "sales": sales,
        "deliveries": deliveries
    })

@router.post("/create")
def create_delivery(
    sale_id: int = Form(...),
    delivery_address: str = Form(...),
    db: Session = Depends(get_db)
):
    delivery = Delivery(
        sale_id=sale_id,
        delivery_address=delivery_address,
        delivery_status="PENDING"
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    sale_items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    for item in sale_items:
        di = DeliveryItem(
            delivery_id=delivery.delivery_id,
            sale_item_id=item.sale_item_id,
            quantity_delivered=item.quantity
        )
        db.add(di)

    db.commit()
    return RedirectResponse(url="/delivery/", status_code=303)

@router.post("/update-status")
def update_delivery_status(
    delivery_id: int = Form(...),
    delivery_status: str = Form(...),
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.delivery_id == delivery_id).first()
    if delivery:
        delivery.delivery_status = delivery_status
        db.commit()

    return RedirectResponse(url="/delivery/", status_code=303)