import random
from decimal import Decimal
from datetime import date, timedelta

from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from faker import Faker

from ..db import get_db
from .. import models
from ..utils.accounting import post_journal_entry

router = APIRouter(prefix="/seed", tags=["Seed"])
templates = Jinja2Templates(directory="app/templates")

fake = Faker()


# =========================================================
# HELPERS
# =========================================================
def random_past_date(days_back=365):
    return date.today() - timedelta(days=random.randint(0, days_back))


def dec(v):
    return Decimal(str(round(v, 2)))


# =========================================================
# PAGE
# =========================================================
@router.get("/")
def seed_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="seed.html",
        context={
            "request": request,
            "message": None,
            "error": None
        }
    )


# =========================================================
# SEED BUSINESS PARTNERS
# =========================================================
@router.post("/partners")
def seed_partners(
    request: Request,
    customer_count: int = Form(30),
    supplier_count: int = Form(10),
    tenant_count: int = Form(5),
    db: Session = Depends(get_db),
):
    try:
        # Customers
        for i in range(customer_count):
            code = f"CUST-{fake.unique.random_int(10000, 99999)}"
            bp = models.BusinessPartner(
                partner_code=code,
                name=fake.name(),
                partner_type="Individual",
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_customer=True,
                is_supplier=False,
                is_tenant=False,
            )
            db.add(bp)
            db.flush()

            db.add(models.Customer(
                business_partner_id=bp.id,
                customer_group=random.choice(["Retail", "VIP", "Corporate"])
            ))

        # Suppliers
        for i in range(supplier_count):
            code = f"SUP-{fake.unique.random_int(10000, 99999)}"
            bp = models.BusinessPartner(
                partner_code=code,
                name=fake.company(),
                partner_type="Company",
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_customer=False,
                is_supplier=True,
                is_tenant=False,
            )
            db.add(bp)
            db.flush()

            db.add(models.Supplier(
                business_partner_id=bp.id,
                supplier_category=random.choice(["Apparel", "Electronics", "Home", "Beauty"])
            ))

        # Tenants
        for i in range(tenant_count):
            code = f"TEN-{fake.unique.random_int(10000, 99999)}"
            start_date = random_past_date(730)
            end_date = start_date + timedelta(days=365 * random.randint(1, 3))

            bp = models.BusinessPartner(
                partner_code=code,
                name=fake.company(),
                partner_type="Company",
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_customer=False,
                is_supplier=False,
                is_tenant=True,
            )
            db.add(bp)
            db.flush()

            db.add(models.Tenant(
                business_partner_id=bp.id,
                lease_start_date=start_date,
                lease_end_date=end_date
            ))

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": f"Seeded {customer_count} customers, {supplier_count} suppliers, {tenant_count} tenants.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )


# =========================================================
# SEED INVENTORY
# =========================================================
@router.post("/inventory")
def seed_inventory(
    request: Request,
    item_count: int = Form(50),
    db: Session = Depends(get_db),
):
    try:
        categories = ["Apparel", "Electronics", "Home", "Beauty", "Sports", "Toys"]

        for i in range(item_count):
            sku = f"SKU-{fake.unique.random_int(100000, 999999)}"
            cost = dec(random.uniform(5, 200))
            price = dec(float(cost) * random.uniform(1.2, 2.5))
            qty = dec(random.randint(10, 200))

            item = models.Inventory(
                sku=sku,
                product_name=f"{random.choice(categories)} {fake.word().title()}",
                category=random.choice(categories),
                unit_price=price,
                unit_cost=cost,
                quantity_on_hand=qty,
                is_active=True
            )
            db.add(item)
            db.flush()

            opening_value = qty * cost

            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "1200", "Inventory", debit=opening_value)
            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "3000", "Opening Equity Adjustment", credit=opening_value)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": f"Seeded {item_count} inventory items.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )


# =========================================================
# SEED SALES
# =========================================================
@router.post("/sales")
def seed_sales(
    request: Request,
    sale_count: int = Form(100),
    db: Session = Depends(get_db),
):
    try:
        customers = db.query(models.Customer).all()
        inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

        if not customers or not inventory_items:
            raise ValueError("You need seeded customers and inventory first.")

        created = 0

        for _ in range(sale_count):
            inventory = random.choice(inventory_items)

            available_stock = Decimal(str(inventory.quantity_on_hand or 0))
            if available_stock <= 1:
                continue

            customer = random.choice(customers)
            qty = dec(random.randint(1, min(5, int(available_stock))))
            price = Decimal(str(inventory.unit_price))
            cost = Decimal(str(inventory.unit_cost))
            sale_dt = random_past_date(180)
            payment_method = random.choice(["cash", "credit"])

            total_amount = qty * price
            cogs_total = qty * cost

            sale = models.Sales(
                customer_id=customer.id,
                sale_date=sale_dt,
                total_amount=total_amount,
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
                line_total=total_amount
            ))

            inventory.quantity_on_hand = available_stock - qty

            if payment_method == "credit":
                db.add(models.AccountsReceivable(
                    customer_id=customer.id,
                    sale_id=sale.id,
                    amount_due=total_amount,
                    due_date=sale_dt + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, sale_dt, "SALE", sale.id, "1100", "Accounts Receivable", debit=total_amount)
            else:
                post_journal_entry(db, sale_dt, "SALE", sale.id, "1000", "Cash / Treasury", debit=total_amount)

            post_journal_entry(db, sale_dt, "SALE", sale.id, "4000", "Sales Revenue", credit=total_amount)
            post_journal_entry(db, sale_dt, "SALE", sale.id, "5000", "Cost of Goods Sold", debit=cogs_total)
            post_journal_entry(db, sale_dt, "SALE", sale.id, "1200", "Inventory", credit=cogs_total)

            created += 1

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": f"Seeded {created} sales transactions.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )


# =========================================================
# SEED PURCHASES
# =========================================================
@router.post("/purchases")
def seed_purchases(
    request: Request,
    purchase_count: int = Form(80),
    db: Session = Depends(get_db),
):
    try:
        suppliers = db.query(models.Supplier).all()
        inventory_items = db.query(models.Inventory).filter(models.Inventory.is_active == True).all()

        if not suppliers or not inventory_items:
            raise ValueError("You need seeded suppliers and inventory first.")

        for _ in range(purchase_count):
            supplier = random.choice(suppliers)
            inventory = random.choice(inventory_items)

            qty = dec(random.randint(5, 30))
            cost = dec(random.uniform(5, 200))
            total_amount = qty * cost
            purchase_dt = random_past_date(180)
            payment_method = random.choice(["cash", "credit"])

            purchase = models.Purchases(
                supplier_id=supplier.id,
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

            inventory.quantity_on_hand = Decimal(str(inventory.quantity_on_hand or 0)) + qty
            inventory.unit_cost = cost

            post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1200", "Inventory", debit=total_amount)

            if payment_method == "credit":
                db.add(models.AccountsPayable(
                    supplier_id=supplier.id,
                    purchase_id=purchase.id,
                    amount_due=total_amount,
                    due_date=purchase_dt + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "2100", "Accounts Payable", credit=total_amount)
            else:
                post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1000", "Cash / Treasury", credit=total_amount)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": f"Seeded {purchase_count} purchase transactions.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )


# =========================================================
# SEED ASSETS
# =========================================================
@router.post("/assets")
def seed_assets(
    request: Request,
    asset_count: int = Form(20),
    db: Session = Depends(get_db),
):
    try:
        suppliers = db.query(models.Supplier).all()
        categories = ["IT Equipment", "Furniture", "Store Fixtures", "Office Equipment"]

        for _ in range(asset_count):
            supplier = random.choice(suppliers) if suppliers else None
            acq_date = random_past_date(730)
            cost = dec(random.uniform(500, 20000))
            salvage = dec(float(cost) * random.uniform(0.0, 0.1))
            useful_life = random.choice([24, 36, 48, 60])
            payment_method = random.choice(["cash", "credit"])

            asset = models.Asset(
                asset_code=f"AST-{fake.unique.random_int(10000, 99999)}",
                asset_name=f"{random.choice(categories)} {fake.word().title()}",
                category=random.choice(categories),
                acquisition_date=acq_date,
                acquisition_cost=cost,
                useful_life_months=useful_life,
                salvage_value=salvage,
                status="Active"
            )
            db.add(asset)
            db.flush()

            post_journal_entry(db, acq_date, "ASSET", asset.id, "1500", "Fixed Assets", debit=cost)

            if payment_method == "credit" and supplier:
                db.add(models.AccountsPayable(
                    supplier_id=supplier.id,
                    purchase_id=None,
                    amount_due=cost,
                    due_date=acq_date + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, acq_date, "ASSET", asset.id, "2100", "Accounts Payable", credit=cost)
            else:
                post_journal_entry(db, acq_date, "ASSET", asset.id, "1000", "Cash / Treasury", credit=cost)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": f"Seeded {asset_count} assets.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )


# =========================================================
# SEED EVERYTHING
# =========================================================
@router.post("/all")
def seed_all(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        # --- Partners ---
        for _ in range(30):
            code = f"CUST-{fake.unique.random_int(10000, 99999)}"
            bp = models.BusinessPartner(
                partner_code=code,
                name=fake.name(),
                partner_type="Individual",
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_customer=True
            )
            db.add(bp)
            db.flush()
            db.add(models.Customer(business_partner_id=bp.id, customer_group=random.choice(["Retail", "VIP", "Corporate"])))

        for _ in range(10):
            code = f"SUP-{fake.unique.random_int(10000, 99999)}"
            bp = models.BusinessPartner(
                partner_code=code,
                name=fake.company(),
                partner_type="Company",
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
                is_supplier=True
            )
            db.add(bp)
            db.flush()
            db.add(models.Supplier(business_partner_id=bp.id, supplier_category=random.choice(["Apparel", "Electronics", "Home", "Beauty"])))

        db.flush()

        # --- Inventory ---
        categories = ["Apparel", "Electronics", "Home", "Beauty", "Sports", "Toys"]
        for _ in range(50):
            sku = f"SKU-{fake.unique.random_int(100000, 999999)}"
            cost = dec(random.uniform(5, 200))
            price = dec(float(cost) * random.uniform(1.2, 2.5))
            qty = dec(random.randint(10, 200))

            item = models.Inventory(
                sku=sku,
                product_name=f"{random.choice(categories)} {fake.word().title()}",
                category=random.choice(categories),
                unit_price=price,
                unit_cost=cost,
                quantity_on_hand=qty,
                is_active=True
            )
            db.add(item)
            db.flush()

            opening_value = qty * cost
            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "1200", "Inventory", debit=opening_value)
            post_journal_entry(db, date.today(), "INVENTORY_OPENING", item.id, "3000", "Opening Equity Adjustment", credit=opening_value)

        db.flush()

        customers = db.query(models.Customer).all()
        suppliers = db.query(models.Supplier).all()
        inventory_items = db.query(models.Inventory).all()

        # --- Sales ---
        for _ in range(100):
            inventory = random.choice(inventory_items)
            available_stock = Decimal(str(inventory.quantity_on_hand or 0))
            if available_stock <= 1:
                continue

            customer = random.choice(customers)
            qty = dec(random.randint(1, min(5, int(available_stock))))
            price = Decimal(str(inventory.unit_price))
            cost = Decimal(str(inventory.unit_cost))
            sale_dt = random_past_date(180)
            payment_method = random.choice(["cash", "credit"])

            total_amount = qty * price
            cogs_total = qty * cost

            sale = models.Sales(
                customer_id=customer.id,
                sale_date=sale_dt,
                total_amount=total_amount,
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
                line_total=total_amount
            ))

            inventory.quantity_on_hand = available_stock - qty

            if payment_method == "credit":
                db.add(models.AccountsReceivable(
                    customer_id=customer.id,
                    sale_id=sale.id,
                    amount_due=total_amount,
                    due_date=sale_dt + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, sale_dt, "SALE", sale.id, "1100", "Accounts Receivable", debit=total_amount)
            else:
                post_journal_entry(db, sale_dt, "SALE", sale.id, "1000", "Cash / Treasury", debit=total_amount)

            post_journal_entry(db, sale_dt, "SALE", sale.id, "4000", "Sales Revenue", credit=total_amount)
            post_journal_entry(db, sale_dt, "SALE", sale.id, "5000", "Cost of Goods Sold", debit=cogs_total)
            post_journal_entry(db, sale_dt, "SALE", sale.id, "1200", "Inventory", credit=cogs_total)

        # --- Purchases ---
        for _ in range(80):
            supplier = random.choice(suppliers)
            inventory = random.choice(inventory_items)

            qty = dec(random.randint(5, 30))
            cost = dec(random.uniform(5, 200))
            total_amount = qty * cost
            purchase_dt = random_past_date(180)
            payment_method = random.choice(["cash", "credit"])

            purchase = models.Purchases(
                supplier_id=supplier.id,
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

            inventory.quantity_on_hand = Decimal(str(inventory.quantity_on_hand or 0)) + qty
            inventory.unit_cost = cost

            post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1200", "Inventory", debit=total_amount)

            if payment_method == "credit":
                db.add(models.AccountsPayable(
                    supplier_id=supplier.id,
                    purchase_id=purchase.id,
                    amount_due=total_amount,
                    due_date=purchase_dt + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "2100", "Accounts Payable", credit=total_amount)
            else:
                post_journal_entry(db, purchase_dt, "PURCHASE", purchase.id, "1000", "Cash / Treasury", credit=total_amount)

        # --- Assets ---
        asset_categories = ["IT Equipment", "Furniture", "Store Fixtures", "Office Equipment"]
        for _ in range(20):
            supplier = random.choice(suppliers) if suppliers else None
            acq_date = random_past_date(730)
            cost = dec(random.uniform(500, 20000))
            salvage = dec(float(cost) * random.uniform(0.0, 0.1))
            useful_life = random.choice([24, 36, 48, 60])
            payment_method = random.choice(["cash", "credit"])

            asset = models.Asset(
                asset_code=f"AST-{fake.unique.random_int(10000, 99999)}",
                asset_name=f"{random.choice(asset_categories)} {fake.word().title()}",
                category=random.choice(asset_categories),
                acquisition_date=acq_date,
                acquisition_cost=cost,
                useful_life_months=useful_life,
                salvage_value=salvage,
                status="Active"
            )
            db.add(asset)
            db.flush()

            post_journal_entry(db, acq_date, "ASSET", asset.id, "1500", "Fixed Assets", debit=cost)

            if payment_method == "credit" and supplier:
                db.add(models.AccountsPayable(
                    supplier_id=supplier.id,
                    purchase_id=None,
                    amount_due=cost,
                    due_date=acq_date + timedelta(days=30),
                    status="Open"
                ))
                post_journal_entry(db, acq_date, "ASSET", asset.id, "2100", "Accounts Payable", credit=cost)
            else:
                post_journal_entry(db, acq_date, "ASSET", asset.id, "1000", "Cash / Treasury", credit=cost)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": "Seeded everything successfully.",
                "error": None
            }
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="seed.html",
            context={
                "request": request,
                "message": None,
                "error": str(e)
            }
        )