from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class InventoryBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    unit: Optional[str] = "pcs"
    cost_price: float = 0
    selling_price: float = 0
    quantity_on_hand: int = 0
    reorder_level: int = 10


class InventoryCreate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    id: int

    class Config:
        from_attributes = True


class BusinessPartnerBase(BaseModel):
    partner_code: str
    name: str
    partner_type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class BusinessPartnerCreate(BusinessPartnerBase):
    pass


class BusinessPartnerRead(BusinessPartnerBase):
    id: int

    class Config:
        from_attributes = True


class SaleItemCreate(BaseModel):
    inventory_id: int
    quantity: int
    unit_price: float


class SaleCreate(BaseModel):
    customer_partner_id: Optional[int] = None
    member_id: Optional[int] = None
    payment_method: str = "CASH"
    discount_amount: float = 0
    tax_amount: float = 0
    items: List[SaleItemCreate]


class SaleRead(BaseModel):
    id: int
    sale_no: str
    net_amount: float
    payment_method: str
    status: str

    class Config:
        from_attributes = True


class PurchaseItemCreate(BaseModel):
    inventory_id: int
    quantity: int
    unit_cost: float


class PurchaseCreate(BaseModel):
    supplier_partner_id: int
    tax_amount: float = 0
    items: List[PurchaseItemCreate]


class PurchaseRead(BaseModel):
    id: int
    purchase_no: str
    net_amount: float
    status: str

    class Config:
        from_attributes = True