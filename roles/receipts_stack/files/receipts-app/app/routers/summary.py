from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("/months", response_model=list[schemas.MonthSummary])
def months_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            extract("year", models.Receipt.purchase_date).label("y"),
            extract("month", models.Receipt.purchase_date).label("m"),
            func.count(func.distinct(models.Receipt.id)).label("receipt_count"),
            func.coalesce(func.sum(models.LineItem.price), 0).label("total"),
        )
        .join(models.LineItem, models.LineItem.receipt_id == models.Receipt.id, isouter=True)
        .filter(models.Receipt.purchase_date.isnot(None))
        .group_by("y", "m")
        .order_by("y", "m")
        .all()
    )
    return [
        schemas.MonthSummary(
            month=f"{int(r.y):04d}-{int(r.m):02d}",
            total=Decimal(r.total),
            receipt_count=r.receipt_count,
        )
        for r in rows
    ]


@router.get("/{month}", response_model=list[schemas.CategoryBreakdown])
def category_breakdown(month: str, db: Session = Depends(get_db)):
    year, mo = month.split("-")
    rows = (
        db.query(
            models.Category.name.label("category"),
            func.coalesce(models.Category.color, "#6b7280").label("color"),
            func.sum(models.LineItem.price).label("total"),
        )
        .select_from(models.LineItem)
        .join(models.Receipt, models.Receipt.id == models.LineItem.receipt_id)
        .outerjoin(models.Category, models.Category.id == models.LineItem.category_id)
        .filter(
            extract("year", models.Receipt.purchase_date) == int(year),
            extract("month", models.Receipt.purchase_date) == int(mo),
        )
        .group_by(models.Category.name, models.Category.color)
        .order_by(func.sum(models.LineItem.price).desc())
        .all()
    )
    return [
        schemas.CategoryBreakdown(category=r.category, color=r.color, total=Decimal(r.total))
        for r in rows
    ]
