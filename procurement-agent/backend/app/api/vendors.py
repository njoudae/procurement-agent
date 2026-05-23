from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import VendorCreate, VendorRead, VendorUpdate
from app.security import require_admin
from app.tools.vendor_tools import create_vendor, list_vendors, update_vendor

router = APIRouter(prefix="/vendors", tags=["vendors"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[VendorRead])
def get_vendors(db: Session = Depends(get_db)):
    return list_vendors(db)


@router.post("", response_model=VendorRead)
def add_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    return create_vendor(db, payload)


@router.put("/{vendor_id}", response_model=VendorRead)
def edit_vendor(vendor_id: int, payload: VendorUpdate, db: Session = Depends(get_db)):
    vendor = update_vendor(db, vendor_id, payload)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor
