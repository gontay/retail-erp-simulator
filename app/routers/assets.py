from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..utils.accounting import post_journal_entry

router = APIRouter(prefix="/assets", tags=["Assets"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def asset_form(request: Request, db: Session = Depends(get_db)):
    suppliers = db.query(models.Supplier).all()
    assets = db.query(models.Asset).all()

    return templates.TemplateResponse(
        name="assets.html",
        request=request,
        context= {
        "request": request,
        "suppliers": suppliers,
        "assets": assets,
        "message": None,
        "error": None
    })


@router.post("/new")
def submit_asset(
    request: Request,
    asset_code: str = Form(...),
    asset_name: str = Form(...),
    category: str = Form(...),
    acquisition_date: str = Form(...),
    acquisition_cost: float = Form(...),
    useful_life_months: int = Form(...),
    salvage_value: float = Form(...),
    payment_method: str = Form(...),
    supplier_id: int = Form(None),
    db: Session = Depends(get_db),
):
    suppliers = db.query(models.Supplier).all()
    assets = db.query(models.Asset).all()

    try:
        acq_date = datetime.strptime(acquisition_date, "%Y-%m-%d").date()
        cost = Decimal(str(acquisition_cost))
        salvage = Decimal(str(salvage_value))

        asset = models.Asset(
            asset_code=asset_code,
            asset_name=asset_name,
            category=category,
            acquisition_date=acq_date,
            acquisition_cost=cost,
            useful_life_months=useful_life_months,
            salvage_value=salvage,
            status="Active"
        )
        db.add(asset)
        db.flush()

        post_journal_entry(db, acq_date, "ASSET", asset.id, "1500", "Fixed Assets", debit=cost)

        if payment_method.lower() == "credit":
            post_journal_entry(db, acq_date, "ASSET", asset.id, "2100", "Accounts Payable", credit=cost)
            if supplier_id:
                db.add(models.AccountsPayable(
                    supplier_id=supplier_id,
                    purchase_id=None,
                    amount_due=cost,
                    due_date=acq_date,
                    status="Open"
                ))
        else:
            post_journal_entry(db, acq_date, "ASSET", asset.id, "1000", "Cash / Treasury", credit=cost)

        db.commit()

        return templates.TemplateResponse(
            name="assets.html",
            request=request,
            context= {
                "request": request,
                "suppliers": suppliers,
                "assets": assets,
                "message": f"Asset '{asset.asset_name}' created successfully.",
                "error": None
            })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            name="assets.html",
            request=request,
            context={
            "request": request,
            "suppliers": suppliers,
            "assets": assets,
            "message": None,
            "error": str(e)
        })


@router.post("/depreciate")
def depreciate_asset(
    request: Request,
    asset_id: int = Form(...),
    depreciation_date: str = Form(...),
    db: Session = Depends(get_db),
):
    suppliers = db.query(models.Supplier).all()
    assets = db.query(models.Asset).all()

    try:
        dep_date = datetime.strptime(depreciation_date, "%Y-%m-%d").date()

        asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
        if not asset:
            raise ValueError("Asset not found.")

        depreciable_base = Decimal(str(asset.acquisition_cost)) - Decimal(str(asset.salvage_value))
        monthly_dep = depreciable_base / Decimal(str(asset.useful_life_months))

        db.add(models.Depreciation(
            asset_id=asset.id,
            depreciation_date=dep_date,
            depreciation_amount=monthly_dep
        ))

        post_journal_entry(db, dep_date, "DEPRECIATION", asset.id, "6100", "Depreciation Expense", debit=monthly_dep)
        post_journal_entry(db, dep_date, "DEPRECIATION", asset.id, "1510", "Accumulated Depreciation", credit=monthly_dep)

        db.commit()

        return templates.TemplateResponse(
            name="assets.html",
            request=request,
            context= {
            "request": request,
            "suppliers": suppliers,
            "assets": assets,
            "message": f"Depreciation posted successfully for Asset ID {asset_id}.",
            "error": None
        })

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            name="assets.html",
            request=request,
            context= {
            "request": request,
            "suppliers": suppliers,
            "assets": assets,
            "message": None,
            "error": str(e)
        })