from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, Text, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


# =========================
# MASTER DATA
# =========================

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    unit = Column(String(20), default="pcs")
    cost_price = Column(Numeric(12, 2), default=0)
    selling_price = Column(Numeric(12, 2), default=0)
    quantity_on_hand = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sale_items = relationship("SaleItem", back_populates="inventory_item")
    purchase_items = relationship("PurchaseItem", back_populates="inventory_item")
    deliveries = relationship("Delivery", back_populates="inventory_item")


class BusinessPartner(Base):
    __tablename__ = "business_partner"

    id = Column(Integer, primary_key=True, index=True)
    partner_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    partner_type = Column(String(50), nullable=False)  # SUPPLIER / CUSTOMER / TENANT / MIXED
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    credit_limit = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("Supplier", back_populates="partner", uselist=False)
    customer = relationship("Customer", back_populates="partner", uselist=False)
    tenant = relationship("Tenant", back_populates="partner", uselist=False)

    sales = relationship("Sales", back_populates="customer_partner", foreign_keys="Sales.customer_partner_id")
    purchases = relationship("Purchases", back_populates="supplier_partner", foreign_keys="Purchases.supplier_partner_id")
    deliveries = relationship("Delivery", back_populates="business_partner")


class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("business_partner.id"), unique=True)
    supplier_rating = Column(String(20))
    payment_terms_days = Column(Integer, default=30)

    partner = relationship("BusinessPartner", back_populates="supplier")


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("business_partner.id"), unique=True)
    loyalty_tier = Column(String(50), default="Standard")

    partner = relationship("BusinessPartner", back_populates="customer")
    member = relationship("Member", back_populates="customer", uselist=False)


class Tenant(Base):
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("business_partner.id"), unique=True)
    shop_name = Column(String(255))
    rental_rate = Column(Numeric(12, 2), default=0)
    lease_start = Column(Date)
    lease_end = Column(Date)

    partner = relationship("BusinessPartner", back_populates="tenant")


class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, index=True)
    member_code = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customer.id"), unique=True)
    join_date = Column(Date)
    points_balance = Column(Integer, default=0)
    membership_status = Column(String(50), default="Active")

    customer = relationship("Customer", back_populates="member")


# =========================
# SALES
# =========================

class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_no = Column(String(50), unique=True, nullable=False, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now())
    customer_partner_id = Column(Integer, ForeignKey("business_partner.id"), nullable=True)
    member_id = Column(Integer, ForeignKey("member.id"), nullable=True)
    payment_method = Column(String(50), default="CASH")
    gross_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    net_amount = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="POSTED")

    customer_partner = relationship("BusinessPartner", back_populates="sales", foreign_keys=[customer_partner_id])
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sales", back_populates="items")
    inventory_item = relationship("Inventory", back_populates="sale_items")


# =========================
# PURCHASING
# =========================

class Purchases(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_no = Column(String(50), unique=True, nullable=False, index=True)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    supplier_partner_id = Column(Integer, ForeignKey("business_partner.id"))
    gross_amount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    net_amount = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="POSTED")

    supplier_partner = relationship("BusinessPartner", back_populates="purchases", foreign_keys=[supplier_partner_id])
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchases", back_populates="items")
    inventory_item = relationship("Inventory", back_populates="purchase_items")


# =========================
# DELIVERY / LOGISTICS
# =========================

class Delivery(Base):
    __tablename__ = "delivery"

    id = Column(Integer, primary_key=True, index=True)
    delivery_no = Column(String(50), unique=True, nullable=False)
    delivery_type = Column(String(50))  # INBOUND / OUTBOUND / INTERNAL
    business_partner_id = Column(Integer, ForeignKey("business_partner.id"), nullable=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Integer, nullable=False)
    delivery_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="DELIVERED")
    remarks = Column(Text)

    business_partner = relationship("BusinessPartner", back_populates="deliveries")
    inventory_item = relationship("Inventory", back_populates="deliveries")


# =========================
# FINANCE
# =========================

class AccountsReceivable(Base):
    __tablename__ = "accounts_receivable"

    id = Column(Integer, primary_key=True, index=True)
    ar_no = Column(String(50), unique=True, nullable=False)
    customer_partner_id = Column(Integer, ForeignKey("business_partner.id"))
    source_sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    invoice_date = Column(Date)
    due_date = Column(Date)
    amount = Column(Numeric(12, 2), default=0)
    balance = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="OPEN")


class AccountsPayable(Base):
    __tablename__ = "accounts_payable"

    id = Column(Integer, primary_key=True, index=True)
    ap_no = Column(String(50), unique=True, nullable=False)
    supplier_partner_id = Column(Integer, ForeignKey("business_partner.id"))
    source_purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    invoice_date = Column(Date)
    due_date = Column(Date)
    amount = Column(Numeric(12, 2), default=0)
    balance = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="OPEN")


class Dunning(Base):
    __tablename__ = "dunning"

    id = Column(Integer, primary_key=True, index=True)
    dunning_no = Column(String(50), unique=True, nullable=False)
    ar_id = Column(Integer, ForeignKey("accounts_receivable.id"))
    dunning_level = Column(Integer, default=1)
    notice_date = Column(Date)
    remarks = Column(Text)


class UniversalJournal(Base):
    __tablename__ = "universal_journal"

    id = Column(Integer, primary_key=True, index=True)
    doc_no = Column(String(50), nullable=False, index=True)
    posting_date = Column(Date, nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    partner_id = Column(Integer, ForeignKey("business_partner.id"), nullable=True)
    reference_type = Column(String(50))  # SALE / PURCHASE / ASSET / CASH / TREASURY
    reference_id = Column(Integer, nullable=True)
    debit = Column(Numeric(12, 2), default=0)
    credit = Column(Numeric(12, 2), default=0)
    description = Column(Text)


class Treasury(Base):
    __tablename__ = "treasury"

    id = Column(Integer, primary_key=True, index=True)
    txn_no = Column(String(50), unique=True, nullable=False)
    txn_date = Column(Date)
    txn_type = Column(String(50))  # BANK_IN / BANK_OUT / TRANSFER
    bank_account = Column(String(100))
    amount = Column(Numeric(12, 2), default=0)
    description = Column(Text)


class CashFloat(Base):
    __tablename__ = "cash_float"

    id = Column(Integer, primary_key=True, index=True)
    float_no = Column(String(50), unique=True, nullable=False)
    txn_date = Column(Date)
    cashier_name = Column(String(255))
    opening_float = Column(Numeric(12, 2), default=0)
    cash_in = Column(Numeric(12, 2), default=0)
    cash_out = Column(Numeric(12, 2), default=0)
    closing_float = Column(Numeric(12, 2), default=0)
    remarks = Column(Text)


# =========================
# FIXED ASSETS
# =========================

class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String(50), unique=True, nullable=False)
    asset_name = Column(String(255), nullable=False)
    category = Column(String(100))
    acquisition_date = Column(Date)
    acquisition_cost = Column(Numeric(12, 2), default=0)
    useful_life_months = Column(Integer, default=60)
    salvage_value = Column(Numeric(12, 2), default=0)
    accumulated_depreciation = Column(Numeric(12, 2), default=0)
    net_book_value = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="ACTIVE")

    depreciations = relationship("Depreciation", back_populates="asset", cascade="all, delete-orphan")


class Depreciation(Base):
    __tablename__ = "depreciation"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id"))
    posting_date = Column(Date)
    depreciation_amount = Column(Numeric(12, 2), default=0)
    accumulated_depreciation = Column(Numeric(12, 2), default=0)
    net_book_value = Column(Numeric(12, 2), default=0)

    asset = relationship("Asset", back_populates="depreciations")