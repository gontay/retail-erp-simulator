from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..db import get_db
from .. import crud,schemas
from ..models import BusinessPartner, Customer, Supplier

router = APIRouter(prefix="/partners", tags=["Partners"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_model=list[schemas.BusinessPartnerRead])
def list_partners(request: Request, db: Session = Depends(get_db)):
    partners = crud.get_business_partners(db)

    # return partners

    return templates.TemplateResponse(
        request=request,
        name="partners.html", 
        context = {
        "partners": partners
    })

@router.post("/create")
def create_partner(
    partner_name: str = Form(...),
    partner_type: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    db: Session = Depends(get_db)
):
    bp = BusinessPartner(
        partner_name=partner_name,
        partner_type=partner_type,
        email=email,
        phone=phone
    )
    db.add(bp)
    db.commit()
    db.refresh(bp)

    if partner_type == "CUSTOMER":
        customer = Customer(
            business_partner_id=bp.business_partner_id,
            customer_type="WALK_IN"
        )
        db.add(customer)

    if partner_type == "SUPPLIER":
        supplier = Supplier(
            business_partner_id=bp.business_partner_id,
            supplier_category="GENERAL"
        )
        db.add(supplier)

    db.commit()
    return RedirectResponse(url="/partners/", status_code=303)