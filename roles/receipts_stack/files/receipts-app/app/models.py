import enum
import os
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class ReceiptStatus(str, enum.Enum):
    processing = "processing"
    needs_review = "needs_review"
    confirmed = "confirmed"
    failed = "failed"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#e3a83b")

    line_items = relationship("LineItem", back_populates="category")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    merchant = Column(String(255))
    purchase_date = Column(Date)
    subtotal = Column(Numeric(10, 2))
    tax = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))
    status = Column(SAEnum(ReceiptStatus), default=ReceiptStatus.processing, nullable=False)
    raw_response = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    line_items = relationship(
        "LineItem", back_populates="receipt", cascade="all, delete-orphan", order_by="LineItem.id"
    )

    @property
    def stored_filename(self) -> str:
        return os.path.basename(self.file_path)


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    receipt = relationship("Receipt", back_populates="line_items")
    category = relationship("Category", back_populates="line_items")
