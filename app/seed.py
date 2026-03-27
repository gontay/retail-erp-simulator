import random
from datetime import date, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.orm import Session

from .db import SessionLocal, Base, engine
from . import models

fake = Faker()


def rand_money(a=10, b=1000):
    return Decimal(str(round(random.uniform(a, b), 2)))


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_inventory(db: Session, count=50):
    categories = ["Fashion", "Beauty", "Electronics", "Home", "Sports", "Food"]
    items = []

    for i in range(count):
        item = models.Inventory(
            sku=f"SKU-{i+1:05d}",
            name=fake.word().capitalize() + " " + random.choice(["Shirt", "Lamp", "Speaker", "Bottle", "Bag", "Watch"]),
            category=random.choice(categories),
            unit="pcs",
            cost_price=rand_money(5, 200),
            selling_price=rand_money(20, 500),
            quantity_on_hand=random.randint(20, 200),
            reorder_level=random.randint(5, 20),
            is_active=True
        )
        db.add(item)
        items.append(item)

    db.commit()
    return items


def seed_partners(db: Session):
    suppliers = []
    customers = []
    tenants = []

    # Suppliers
    for i in range(15):
        bp = models.BusinessPartner(
            partner_code=f"SUP-{i+1:04d}",
            name=fake.company(),
            partner_type="SUPPLIER",
            contact_person=fake.name(),
            email=fake.company_email(),
            phone=fake.phone_number(),
            address=fake.address(),
            credit_limit=rand_money(1000, 20000)
        )
        db.add(bp)
        db.flush()

        supplier = models.Supplier(
            partner_id=bp.id,
            supplier_rating=random.choice(["A", "B", "C"]),
            payment_terms_days=random.choice([30, 45, 60])
        )
        db.add(supplier)
        suppliers.append(bp)

    # Customers + Members
    for i in range(30):
        bp = models.BusinessPartner(
            partner_code=f"CUS-{i+1:04d}",
            name=fake.name(),
            partner_type="CUSTOMER",
            contact_person=fake.name(),
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.address(),
            credit_limit=rand_money(500, 5000)
        )
        db.add(bp)
        db.flush()

        customer = models.Customer(
            partner_id=bp.id,
            loyalty_tier=random.choice(["Standard", "Silver", "Gold", "Platinum"])
        )
        db.add(customer)
        db.flush()

        member = models.Member(
            member_code=f"MEM-{i+1:05d}",
            customer_id=customer.id,
            join_date=fake.date_between(start_date="-3y", end_date="today"),
            points_balance=random.randint(0, 10000),
            membership_status="Active"
        )
        db.add(member)
        customers.append((bp, customer, member))

    # Tenants
    for i in range(10):
        bp = models.BusinessPartner(
            partner_code=f"TEN-{i+1:04d}",
            name=fake.company(),
            partner_type="TENANT",
            contact_person=fake.name(),
            email=fake.company_email(),
            phone=fake.phone_number(),
            address=fake.address(),
            credit_limit=0
        )
        db.add(bp)
        db.flush()

        tenant = models.Tenant(
            partner_id=bp.id,
            shop_name=f"{fake.company()} Boutique",
            rental_rate=rand_money(2000, 15000),
            lease_start=fake.date_between(start_date="-2y", end_date="-1y"),
            lease_end=fake.date_between(start_date="+1y", end_date="+3y")
        )
        db.add(tenant)
        tenants.append(bp)

    db.commit()
    return suppliers, customers, tenants


def seed_purchases(db: Session, suppliers, inventory_items, count=30):
    for i in range(count):
        supplier = random.choice(suppliers)

        purchase = models.Purchases(
            purchase_no=f"PUR-{i+1:06d}",
            purchase_date=fake.date_time_between(start_date="-180d", end_date="now"),
            supplier_partner_id=supplier.id,
            gross_amount=0,
            tax_amount=rand_money(1, 50),
            net_amount=0,
            status="POSTED"
        )
        db.add(purchase)
        db.flush()

        gross = Decimal("0.00")
        lines = random.randint(2, 5)

        for _ in range(lines):
            item = random.choice(inventory_items)
            qty = random.randint(5, 50)
            unit_cost = rand_money(5, 150)
            line_total = Decimal(qty) * unit_cost
            gross += line_total

            item.quantity_on_hand += qty
            item.cost_price = unit_cost

            pi = models.PurchaseItem(
                purchase_id=purchase.id,
                inventory_id=item.id,
                quantity=qty,
                unit_cost=unit_cost,
                line_total=line_total
            )
            db.add(pi)

            delivery = models.Delivery(
                delivery_no=f"DLV-IN-{purchase.id:06d}-{item.id}",
                delivery_type="INBOUND",
                business_partner_id=supplier.id,
                inventory_id=item.id,
                quantity=qty,
                delivery_date=fake.date_time_between(start_date="-180d", end_date="now"),
                status="DELIVERED",
                remarks="Supplier delivery"
            )
            db.add(delivery)

        purchase.gross_amount = gross
        purchase.net_amount = gross + purchase.tax_amount

        ap = models.AccountsPayable(
            ap_no=f"AP-{purchase.id:06d}",
            supplier_partner_id=supplier.id,
            source_purchase_id=purchase.id,
            invoice_date=fake.date_between(start_date="-180d", end_date="today"),
            due_date=fake.date_between(start_date="today", end_date="+45d"),
            amount=purchase.net_amount,
            balance=random.choice([purchase.net_amount, purchase.net_amount / 2, Decimal("0.00")]),
            status=random.choice(["OPEN", "PARTIAL", "PAID"])
        )
        db.add(ap)

        db.add(models.UniversalJournal(
            doc_no=f"UJ-PUR-{purchase.id:06d}",
            posting_date=date.today(),
            account_code="1200",
            account_name="Inventory",
            partner_id=supplier.id,
            reference_type="PURCHASE",
            reference_id=purchase.id,
            debit=purchase.net_amount,
            credit=0,
            description=f"Purchase {purchase.purchase_no}"
        ))
        db.add(models.UniversalJournal(
            doc_no=f"UJ-PUR-{purchase.id:06d}",
            posting_date=date.today(),
            account_code="2000",
            account_name="Accounts Payable",
            partner_id=supplier.id,
            reference_type="PURCHASE",
            reference_id=purchase.id,
            debit=0,
            credit=purchase.net_amount,
            description=f"Purchase {purchase.purchase_no}"
        ))

    db.commit()


def seed_sales(db: Session, customers, inventory_items, count=50):
    for i in range(count):
        bp, customer, member = random.choice(customers)

        sale = models.Sales(
            sale_no=f"SAL-{i+1:06d}",
            sale_date=fake.date_time_between(start_date="-120d", end_date="now"),
            customer_partner_id=bp.id,
            member_id=member.id,
            payment_method=random.choice(["CASH", "CARD", "PAYNOW", "AR"]),
            gross_amount=0,
            discount_amount=rand_money(0, 30),
            tax_amount=rand_money(0, 20),
            net_amount=0,
            status="POSTED"
        )
        db.add(sale)
        db.flush()

        gross = Decimal("0.00")
        lines = random.randint(1, 4)

        for _ in range(lines):
            item = random.choice(inventory_items)
            qty = random.randint(1, 3)

            if item.quantity_on_hand < qty:
                continue

            unit_price = Decimal(item.selling_price)
            line_total = Decimal(qty) * unit_price
            gross += line_total

            item.quantity_on_hand -= qty

            si = models.SaleItem(
                sale_id=sale.id,
                inventory_id=item.id,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total
            )
            db.add(si)

            delivery = models.Delivery(
                delivery_no=f"DLV-OUT-{sale.id:06d}-{item.id}",
                delivery_type="OUTBOUND",
                business_partner_id=bp.id,
                inventory_id=item.id,
                quantity=qty,
                delivery_date=fake.date_time_between(start_date="-120d", end_date="now"),
                status="DELIVERED",
                remarks="Customer fulfilment"
            )
            db.add(delivery)

        sale.gross_amount = gross
        sale.net_amount = gross - sale.discount_amount + sale.tax_amount

        if sale.payment_method == "AR":
            ar = models.AccountsReceivable(
                ar_no=f"AR-{sale.id:06d}",
                customer_partner_id=bp.id,
                source_sale_id=sale.id,
                invoice_date=fake.date_between(start_date="-90d", end_date="today"),
                due_date=fake.date_between(start_date="today", end_date="+30d"),
                amount=sale.net_amount,
                balance=random.choice([sale.net_amount, sale.net_amount / 2, Decimal("0.00")]),
                status=random.choice(["OPEN", "PARTIAL", "PAID"])
            )
            db.add(ar)

        db.add(models.UniversalJournal(
            doc_no=f"UJ-SAL-{sale.id:06d}",
            posting_date=date.today(),
            account_code="1000",
            account_name="Cash / Receivable",
            partner_id=bp.id,
            reference_type="SALE",
            reference_id=sale.id,
            debit=sale.net_amount,
            credit=0,
            description=f"Sale {sale.sale_no}"
        ))
        db.add(models.UniversalJournal(
            doc_no=f"UJ-SAL-{sale.id:06d}",
            posting_date=date.today(),
            account_code="4000",
            account_name="Sales Revenue",
            partner_id=bp.id,
            reference_type="SALE",
            reference_id=sale.id,
            debit=0,
            credit=sale.net_amount,
            description=f"Sale {sale.sale_no}"
        ))

    db.commit()


def seed_dunning(db: Session):
    ars = db.query(models.AccountsReceivable).filter(models.AccountsReceivable.status.in_(["OPEN", "PARTIAL"])).all()

    for i, ar in enumerate(ars[:10], start=1):
        d = models.Dunning(
            dunning_no=f"DUN-{i:05d}",
            ar_id=ar.id,
            dunning_level=random.choice([1, 2, 3]),
            notice_date=fake.date_between(start_date="-30d", end_date="today"),
            remarks="Payment reminder sent"
        )
        db.add(d)

    db.commit()


def seed_assets(db: Session, count=15):
    categories = ["POS", "Furniture", "Computers", "Aircon", "Renovation"]

    for i in range(count):
        cost = rand_money(1000, 25000)
        useful_life = random.choice([36, 48, 60, 84])
        salvage = rand_money(0, 1000)
        monthly_dep = (cost - salvage) / useful_life
        accumulated = monthly_dep * random.randint(1, useful_life // 2)
        nbv = cost - accumulated

        asset = models.Asset(
            asset_code=f"AST-{i+1:05d}",
            asset_name=fake.word().capitalize() + " Asset",
            category=random.choice(categories),
            acquisition_date=fake.date_between(start_date="-5y", end_date="-1y"),
            acquisition_cost=cost,
            useful_life_months=useful_life,
            salvage_value=salvage,
            accumulated_depreciation=accumulated,
            net_book_value=nbv,
            status="ACTIVE"
        )
        db.add(asset)
        db.flush()

        for m in range(1, 4):
            dep_amt = monthly_dep
            dep = models.Depreciation(
                asset_id=asset.id,
                posting_date=date.today() - timedelta(days=30 * m),
                depreciation_amount=dep_amt,
                accumulated_depreciation=accumulated,
                net_book_value=nbv
            )
            db.add(dep)

            db.add(models.UniversalJournal(
                doc_no=f"UJ-AST-{asset.id:06d}-{m}",
                posting_date=date.today(),
                account_code="6100",
                account_name="Depreciation Expense",
                partner_id=None,
                reference_type="ASSET",
                reference_id=asset.id,
                debit=dep_amt,
                credit=0,
                description=f"Depreciation for {asset.asset_code}"
            ))
            db.add(models.UniversalJournal(
                doc_no=f"UJ-AST-{asset.id:06d}-{m}",
                posting_date=date.today(),
                account_code="1600",
                account_name="Accumulated Depreciation",
                partner_id=None,
                reference_type="ASSET",
                reference_id=asset.id,
                debit=0,
                credit=dep_amt,
                description=f"Accumulated depreciation {asset.asset_code}"
            ))

    db.commit()


def seed_treasury_and_cash(db: Session):
    for i in range(20):
        tr = models.Treasury(
            txn_no=f"TR-{i+1:05d}",
            txn_date=fake.date_between(start_date="-90d", end_date="today"),
            txn_type=random.choice(["BANK_IN", "BANK_OUT", "TRANSFER"]),
            bank_account=random.choice(["DBS-001", "OCBC-002", "UOB-003"]),
            amount=rand_money(500, 10000),
            description="Treasury movement"
        )
        db.add(tr)

    for i in range(20):
        opening = rand_money(100, 500)
        cash_in = rand_money(200, 2000)
        cash_out = rand_money(50, 1000)
        cf = models.CashFloat(
            float_no=f"CF-{i+1:05d}",
            txn_date=fake.date_between(start_date="-60d", end_date="today"),
            cashier_name=fake.name(),
            opening_float=opening,
            cash_in=cash_in,
            cash_out=cash_out,
            closing_float=opening + cash_in - cash_out,
            remarks="POS cash float"
        )
        db.add(cf)

    db.commit()


def run_seed():
    create_tables()
    db = SessionLocal()

    try:
        print("Seeding inventory...")
        inventory_items = seed_inventory(db, 60)

        print("Seeding business partners...")
        suppliers, customers, tenants = seed_partners(db)

        print("Seeding purchases...")
        seed_purchases(db, suppliers, inventory_items, 40)

        print("Seeding sales...")
        seed_sales(db, customers, inventory_items, 80)

        print("Seeding dunning...")
        seed_dunning(db)

        print("Seeding assets...")
        seed_assets(db, 20)

        print("Seeding treasury and cash float...")
        seed_treasury_and_cash(db)

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()