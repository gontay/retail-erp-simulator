from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models

router = APIRouter(prefix="/partners", tags=["Business Partners"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def partner_form(request: Request):
    return templates.TemplateResponse(
        request = request,
        name="partners.html",
        context= {
        "request": request,
        "message": None,
        "error": None
    })


@router.post("/new")
def submit_partner(
    request: Request,
    partner_code: str = Form(...),
    name: str = Form(...),
    partner_type: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    is_customer: str = Form(None),
    is_supplier: str = Form(None),
    is_tenant: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        existing = db.query(models.BusinessPartner).filter(models.BusinessPartner.partner_code == partner_code).first()
        if existing:
            raise ValueError("Partner code already exists.")

        bp = models.BusinessPartner(
            partner_code=partner_code,
            name=name,
            partner_type=partner_type,
            email=email or None,
            phone=phone or None,
            address=address or None,
            is_customer=bool(is_customer),
            is_supplier=bool(is_supplier),
            is_tenant=bool(is_tenant),
        )
        db.add(bp)
        db.flush()

        if bp.is_customer:
            db.add(models.Customer(business_partner_id=bp.id))

        if bp.is_supplier:
            db.add(models.Supplier(business_partner_id=bp.id))

        if bp.is_tenant:
            db.add(models.Tenant(business_partner_id=bp.id))

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name = "partners.html",
            context= {
            "request": request,
            "message": f"Business Partner '{name}' created successfully.",
            "error": None
        })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="partners.html",
            context= {
            "request": request,
            "message": None,
            "error": str(e)
        })