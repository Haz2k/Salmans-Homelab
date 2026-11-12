import os
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import extract
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..extraction import extract_receipt

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

DATA_DIR = os.environ.get("RECEIPTS_DATA_DIR", "/data/receipts")


def _safe_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _safe_date(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def process_receipt(receipt_id: str):
    """Background task: call the extraction API and populate the receipt."""
    from ..database import SessionLocal  # local import avoids circulars in bg thread

    db: Session = SessionLocal()
    try:
        receipt = db.get(models.Receipt, uuid.UUID(receipt_id))
        if receipt is None:
            return

        category_names = [c.name for c in db.query(models.Category).all()]

        try:
            result = extract_receipt(receipt.file_path, receipt.filename, category_names)
        except Exception as exc:  # noqa: BLE001 — surfaced to the review screen, not swallowed
            receipt.status = models.ReceiptStatus.failed
            receipt.error_message = str(exc)[:2000]
            db.commit()
            return

        receipt.merchant = result.get("merchant")
        receipt.purchase_date = _safe_date(result.get("purchase_date"))
        receipt.subtotal = _safe_decimal(result.get("subtotal"))
        receipt.tax = _safe_decimal(result.get("tax"))
        receipt.total = _safe_decimal(result.get("total"))
        receipt.raw_response = str(result)

        category = None
        suggested = result.get("suggested_category")
        if suggested:
            category = db.query(models.Category).filter(models.Category.name == suggested).first()

        for item in result.get("items", []):
            price = _safe_decimal(item.get("price"))
            if price is None:
                continue
            db.add(
                models.LineItem(
                    receipt_id=receipt.id,
                    description=str(item.get("description") or "Item")[:255],
                    quantity=_safe_decimal(item.get("quantity")) or Decimal("1"),
                    price=price,
                    category_id=category.id if category else None,
                )
            )

        receipt.status = models.ReceiptStatus.needs_review
        db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=list[schemas.ReceiptOut])
def upload_receipts(
    background_tasks: BackgroundTasks,
    files: list[UploadFile],
    db: Session = Depends(get_db),
):
    created = []
    for upload in files:
        ext = os.path.splitext(upload.filename or "")[1] or ".jpg"
        stored_name = f"{uuid.uuid4()}{ext}"
        dest_path = os.path.join(DATA_DIR, stored_name)

        with open(dest_path, "wb") as f:
            f.write(upload.file.read())

        receipt = models.Receipt(
            filename=upload.filename or stored_name,
            file_path=dest_path,
            status=models.ReceiptStatus.processing,
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        background_tasks.add_task(process_receipt, str(receipt.id))
        created.append(receipt)

    return created


@router.get("", response_model=list[schemas.ReceiptOut])
def list_receipts(month: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Receipt)
    if month:
        year, mo = month.split("-")
        query = query.filter(
            extract("year", models.Receipt.purchase_date) == int(year),
            extract("month", models.Receipt.purchase_date) == int(mo),
        )
    return query.order_by(models.Receipt.purchase_date.desc().nullslast()).all()


@router.get("/{receipt_id}", response_model=schemas.ReceiptOut)
def get_receipt(receipt_id: uuid.UUID, db: Session = Depends(get_db)):
    receipt = db.get(models.Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.put("/{receipt_id}", response_model=schemas.ReceiptOut)
def update_receipt(receipt_id: uuid.UUID, payload: schemas.ReceiptUpdate, db: Session = Depends(get_db)):
    receipt = db.get(models.Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    for field in ("merchant", "purchase_date", "subtotal", "tax", "total"):
        value = getattr(payload, field)
        if value is not None:
            setattr(receipt, field, value)

    if payload.line_items is not None:
        existing_ids = {li.id for li in receipt.line_items}
        kept_ids = {li.id for li in payload.line_items if li.id}

        for li in list(receipt.line_items):
            if li.id not in kept_ids:
                db.delete(li)

        for item in payload.line_items:
            if item.id and item.id in existing_ids:
                target = next(li for li in receipt.line_items if li.id == item.id)
                target.description = item.description
                target.quantity = item.quantity
                target.price = item.price
                target.category_id = item.category_id
            else:
                db.add(
                    models.LineItem(
                        receipt_id=receipt.id,
                        description=item.description,
                        quantity=item.quantity,
                        price=item.price,
                        category_id=item.category_id,
                    )
                )

    if payload.confirm:
        receipt.status = models.ReceiptStatus.confirmed

    db.commit()
    db.refresh(receipt)
    return receipt


@router.delete("/{receipt_id}", status_code=204)
def delete_receipt(receipt_id: uuid.UUID, db: Session = Depends(get_db)):
    receipt = db.get(models.Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if os.path.exists(receipt.file_path):
        os.remove(receipt.file_path)
    db.delete(receipt)
    db.commit()


@router.get("/items/{month}", response_model=list[schemas.LineItemWithReceiptOut])
def list_items_for_month(month: str, db: Session = Depends(get_db)):
    """Flat list of every line item in a given month, newest receipt first —
    for sifting through individual purchases rather than whole receipts."""
    year, mo = month.split("-")
    rows = (
        db.query(models.LineItem, models.Receipt.merchant, models.Receipt.purchase_date)
        .join(models.Receipt, models.Receipt.id == models.LineItem.receipt_id)
        .filter(
            extract("year", models.Receipt.purchase_date) == int(year),
            extract("month", models.Receipt.purchase_date) == int(mo),
        )
        .order_by(models.Receipt.purchase_date.desc().nullslast(), models.LineItem.id.desc())
        .all()
    )
    return [
        schemas.LineItemWithReceiptOut(
            id=item.id,
            description=item.description,
            quantity=item.quantity,
            price=item.price,
            category=item.category,
            receipt_id=item.receipt_id,
            merchant=merchant,
            purchase_date=purchase_date,
        )
        for item, merchant, purchase_date in rows
    ]


@router.delete("/items/{item_id}", status_code=204)
def delete_line_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.LineItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    db.delete(item)
    db.commit()
