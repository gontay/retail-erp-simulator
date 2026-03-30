from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey,
    Numeric, Boolean, Text
)
from sqlalchemy.orm import relationship
from .db import Base


# =========================
# AUDIT MIXIN
# =========================
class AuditMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =========================
# BUSINESS PARTNERS
# =========================
class BusinessPartner(Base, AuditMixin):
    __tablename__ = "business_partners"

    id = Column(Integer, primary_key=True, index=True)
    partner_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    partner_type = Column(String(50), nullable=True)  # Individual / Company
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    is_customer = Column(Boolean, default=False)
    is_supplier = Column(Boolean, default=False)
    is_tenant = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="business_partner", uselist=False)
    supplier = relationship("Supplier", back_populates="business_partner", uselist=False)
    tenant = relationship("Tenant", back_populates="business_partner", uselist=False)


class Customer(Base, AuditMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    business_partner_id = Column(Integer, ForeignKey("business_partners.id"), unique=True, nullable=False)
    customer_group = Column(String(100), nullable=True)

    business_partner = relationship("BusinessPartner", back_populates="customer")
    sales = relationship("Sales", back_populates="customer")
    receivables = relationship("AccountsReceivable", back_populates="customer")


class Supplier(Base, AuditMixin):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    business_partner_id = Column(Integer, ForeignKey("business_partners.id"), unique=True, nullable=False)
    supplier_category = Column(String(100), nullable=True)

    business_partner = relationship("BusinessPartner", back_populates="supplier")
    purchases = relationship("Purchases", back_populates="supplier")
    payables = relationship("AccountsPayable", back_populates="supplier")


class Tenant(Base, AuditMixin):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    business_partner_id = Column(Integer, ForeignKey("business_partners.id"), unique=True, nullable=False)
    lease_start_date = Column(Date, nullable=True)
    lease_end_date = Column(Date, nullable=True)

    business_partner = relationship("BusinessPartner", back_populates="tenant")


# =========================
# INVENTORY / PRODUCTS
# =========================
class Inventory(Base, AuditMixin):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    quantity_on_hand = Column(Numeric(12, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)

    sale_items = relationship("SaleItem", back_populates="inventory")
    purchase_items = relationship("PurchaseItem", back_populates="inventory")


# =========================
# SALES
# =========================
class Sales(Base, AuditMixin):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sale_date = Column(Date, nullable=False, default=date.today)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_method = Column(String(50), nullable=False)  # cash / credit
    status = Column(String(50), nullable=False, default="Completed")

    customer = relationship("Customer", back_populates="sales")
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    receivable = relationship("AccountsReceivable", back_populates="sale", uselist=False)


class SaleItem(Base, AuditMixin):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sales", back_populates="sale_items")
    inventory = relationship("Inventory", back_populates="sale_items")


# =========================
# PURCHASES
# =========================
class Purchases(Base, AuditMixin):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_date = Column(Date, nullable=False, default=date.today)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_method = Column(String(50), nullable=False)  # cash / credit
    status = Column(String(50), nullable=False, default="Received")

    supplier = relationship("Supplier", back_populates="purchases")
    purchase_items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    payable = relationship("AccountsPayable", back_populates="purchase", uselist=False)


class PurchaseItem(Base, AuditMixin):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchases", back_populates="purchase_items")
    inventory = relationship("Inventory", back_populates="purchase_items")


# =========================
# ASSETS
# =========================
class Asset(Base, AuditMixin):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String(50), unique=True, nullable=False)
    asset_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    acquisition_date = Column(Date, nullable=False)
    acquisition_cost = Column(Numeric(12, 2), nullable=False)
    useful_life_months = Column(Integer, nullable=False)
    salvage_value = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="Active")

    depreciation_entries = relationship("Depreciation", back_populates="asset", cascade="all, delete-orphan")


class Depreciation(Base, AuditMixin):
    __tablename__ = "depreciation"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    depreciation_date = Column(Date, nullable=False)
    depreciation_amount = Column(Numeric(12, 2), nullable=False)

    asset = relationship("Asset", back_populates="depreciation_entries")


# =========================
# SUBLEDGER TABLES
# =========================
class AccountsReceivable(Base, AuditMixin):
    __tablename__ = "accounts_receivable"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id"), unique=True, nullable=False)
    amount_due = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Open")

    customer = relationship("Customer", back_populates="receivables")
    sale = relationship("Sales", back_populates="receivable")


class AccountsPayable(Base, AuditMixin):
    __tablename__ = "accounts_payable"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), unique=True, nullable=True)
    amount_due = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="Open")

    supplier = relationship("Supplier", back_populates="payables")
    purchase = relationship("Purchases", back_populates="payable")


# =========================
# GENERAL LEDGER
# =========================
class UniversalJournal(Base, AuditMixin):
    __tablename__ = "universal_journal"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(Date, nullable=False)
    reference_type = Column(String(50), nullable=False)  # SALE / PURCHASE / ASSET / DEPRECIATION
    reference_id = Column(Integer, nullable=False)
    account_code = Column(String(20), nullable=False)
    account_name = Column(String(255), nullable=False)
    debit = Column(Numeric(12, 2), nullable=False, default=0)
    credit = Column(Numeric(12, 2), nullable=False, default=0)
    description = Column(Text, nullable=True)