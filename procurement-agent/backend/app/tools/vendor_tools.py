from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.decorators import handle_tool_errors
from app.models import Vendor
from app.schemas import VendorCreate, VendorUpdate


@handle_tool_errors("search_vendors")
def search_vendors(db: Session, category: str, department: str | None = None) -> list[Vendor]:
    category_like = f"%{category.strip()}%"
    filters = [Vendor.IsActive == True, Vendor.Category.ilike(category_like)]  # noqa: E712
    if department:
        filters.append(or_(Vendor.Department.is_(None), Vendor.Department.ilike(f"%{department.strip()}%")))

    statement = select(Vendor).where(and_(*filters)).order_by(Vendor.Rating.desc(), Vendor.CompanyName.asc())
    return list(db.scalars(statement).all())


def list_vendors(db: Session) -> list[Vendor]:
    return list(db.scalars(select(Vendor).order_by(Vendor.CompanyName.asc())).all())


def create_vendor(db: Session, payload: VendorCreate) -> Vendor:
    vendor = Vendor(
        CompanyName=payload.company_name,
        Category=payload.category,
        Department=payload.department,
        Email=str(payload.email),
        Phone=payload.phone,
        Rating=payload.rating,
        IsActive=payload.is_active,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def update_vendor(db: Session, vendor_id: int, payload: VendorUpdate) -> Vendor | None:
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        return None

    updates = payload.model_dump(exclude_unset=True)
    field_map = {
        "company_name": "CompanyName",
        "category": "Category",
        "department": "Department",
        "email": "Email",
        "phone": "Phone",
        "rating": "Rating",
        "is_active": "IsActive",
    }
    for source, target in field_map.items():
        if source in updates:
            value = updates[source]
            setattr(vendor, target, str(value) if source == "email" and value is not None else value)

    db.commit()
    db.refresh(vendor)
    return vendor
