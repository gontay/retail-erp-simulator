from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from . import models, schemas


def generate_doc(prefix: str, row_id: int) -> str:
    return f"{prefix}-{row_id:06d}"


# =========================
# INVENTORY
# =========================

def create_inventory(db: Session, payload: schemas.InventoryCreate):
    item = models.Inventory(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_inventory(db: Session):
    return db.query(models.Inventory).order_by(models.Inventory.id.desc()).all()


# =========================
# BUSINESS PARTNERS
# =========================

def create_business_partner(db: Session, payload: schemas.BusinessPartnerCreate):
    bp = models.BusinessPartner(**payload.model_dump())
    db.add(bp)
    db.commit()
    db.refresh(bp)
    return bp


def get_business_partners(db: Session):
    return db.query(models.BusinessPartner).order_by(models.BusinessPartner.id.desc()).all()


# =========================
# SALES
# =========================

def create_sale(db: Session, payload: schemas.SaleCreate):
    gross = Decimal("0.00")
    sale = models.Sales(
        customer_partner_id=payload.customer_partner_id,
        member_id=payload.member_id,
        payment_method=payload.payment_method,
        discount_amount=Decimal(str(payload.discount_amount)),
        tax_amount=Decimal(str(payload.tax_amount)),
        status="POSTED"
    )
    db.add(sale)
    db.flush()

    sale.sale_no = generate_doc("SAL", sale.id)

    for row in payload.items:
        line_total = Decimal(str(row.quantity)) * Decimal(str(row.unit_price))
        gross += line_total

        item = db.query(models.Inventory).filter(models.Inventory.id == row.inventory_id).first()
        if not item:
            raise ValueError(f"Inventory item {row.inventory_id} not found")
        if item.quantity_on_hand < row.quantity:
            raise ValueError(f"Insufficient stock for {item.name}")

        item.quantity_on_hand -= row.quantity

        sale_item = models.SaleItem(
            sale_id=sale.id,
            inventory_id=row.inventory_id,
            quantity=row.quantity,
            unit_price=Decimal(str(row.unit_price)),
            line_total=line_total
        )
        db.add(sale_item)

    sale.gross_amount = gross
    sale.net_amount = gross - sale.discount_amount + sale.tax_amount

    db.commit()
    db.refresh(sale)

    create_sale_journal(db, sale)

    return sale


def get_sales(db: Session):
    return db.query(models.Sales).order_by(models.Sales.id.desc()).all()


def create_sale_journal(db: Session, sale: models.Sales):
    doc_no = f"UJ-SALE-{sale.id:06d}"

    entries = [
        models.UniversalJournal(
            doc_no=doc_no,
            posting_date=date.today(),
            account_code="1000",
            account_name="Cash / Receivable",
            partner_id=sale.customer_partner_id,
            reference_type="SALE",
            reference_id=sale.id,
            debit=sale.net_amount,
            credit=0,
            description=f"Sale posting {sale.sale_no}"
        ),
        models.UniversalJournal(
            doc_no=doc_no,
            posting_date=date.today(),
            account_code="4000",
            account_name="Sales Revenue",
            partner_id=sale.customer_partner_id,
            reference_type="SALE",
            reference_id=sale.id,
            debit=0,
            credit=sale.net_amount,
            description=f"Sale revenue {sale.sale_no}"
        )
    ]

    for e in entries:
        db.add(e)
    db.commit()


# =========================
# PURCHASES
# =========================

def create_purchase(db: Session, payload: schemas.PurchaseCreate):
    gross = Decimal("0.00")

    purchase = models.Purchases(
        supplier_partner_id=payload.supplier_partner_id,
        tax_amount=Decimal(str(payload.tax_amount)),
        status="POSTED"
    )
    db.add(purchase)
    db.flush()

    purchase.purchase_no = generate_doc("PUR", purchase.id)

    for row in payload.items:
        line_total = Decimal(str(row.quantity)) * Decimal(str(row.unit_cost))
        gross += line_total

        item = db.query(models.Inventory).filter(models.Inventory.id == row.inventory_id).first()
        if not item:
            raise ValueError(f"Inventory item {row.inventory_id} not found")

        item.quantity_on_hand += row.quantity
        item.cost_price = Decimal(str(row.unit_cost))

        purchase_item = models.PurchaseItem(
            purchase_id=purchase.id,
            inventory_id=row.inventory_id,
            quantity=row.quantity,
            unit_cost=Decimal(str(row.unit_cost)),
            line_total=line_total
        )
        db.add(purchase_item)

    purchase.gross_amount = gross
    purchase.net_amount = gross + purchase.tax_amount

    db.commit()
    db.refresh(purchase)

    create_purchase_journal(db, purchase)
    create_ap_from_purchase(db, purchase)

    return purchase


def get_purchases(db: Session):
    return db.query(models.Purchases).order_by(models.Purchases.id.desc()).all()


def create_purchase_journal(db: Session, purchase: models.Purchases):
    doc_no = f"UJ-PUR-{purchase.id:06d}"

    entries = [
        models.UniversalJournal(
            doc_no=doc_no,
            posting_date=date.today(),
            account_code="1200",
            account_name="Inventory",
            partner_id=purchase.supplier_partner_id,
            reference_type="PURCHASE",
            reference_id=purchase.id,
            debit=purchase.net_amount,
            credit=0,
            description=f"Purchase posting {purchase.purchase_no}"
        ),
        models.UniversalJournal(
            doc_no=doc_no,
            posting_date=date.today(),
            account_code="2000",
            account_name="Accounts Payable",
            partner_id=purchase.supplier_partner_id,
            reference_type="PURCHASE",
            reference_id=purchase.id,
            debit=0,
            credit=purchase.net_amount,
            description=f"AP posting {purchase.purchase_no}"
        )
    ]

    for e in entries:
        db.add(e)
    db.commit()


def create_ap_from_purchase(db: Session, purchase: models.Purchases):
    ap = models.AccountsPayable(
        ap_no=f"AP-{purchase.id:06d}",
        supplier_partner_id=purchase.supplier_partner_id,
        source_purchase_id=purchase.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        amount=purchase.net_amount,
        balance=purchase.net_amount,
        status="OPEN"
    )
    db.add(ap)
    db.commit()