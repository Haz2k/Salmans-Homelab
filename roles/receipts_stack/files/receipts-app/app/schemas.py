import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: str


class CategoryCreate(BaseModel):
    name: str
    color: str = "#e3a83b"


class LineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    description: str
    quantity: Decimal
    price: Decimal
    category_id: Optional[int] = None
    category: Optional[CategoryOut] = None


class LineItemUpdate(BaseModel):
    id: Optional[int] = None  # omit for a new line item
    description: str
    quantity: Decimal = Decimal("1")
    price: Decimal
    category_id: Optional[int] = None


class LineItemWithReceiptOut(BaseModel):
    id: int
    description: str
    quantity: Decimal
    price: Decimal
    category: Optional[CategoryOut] = None
    receipt_id: uuid.UUID
    merchant: Optional[str] = None
    purchase_date: Optional[date] = None


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    stored_filename: str
    merchant: Optional[str] = None
    purchase_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    line_items: list[LineItemOut] = []


class ReceiptUpdate(BaseModel):
    merchant: Optional[str] = None
    purchase_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    line_items: Optional[list[LineItemUpdate]] = None
    confirm: bool = False


class MonthSummary(BaseModel):
    month: str  # "YYYY-MM"
    total: Decimal
    receipt_count: int


class CategoryBreakdown(BaseModel):
    category: Optional[str] = None
    color: str
    total: Decimal
