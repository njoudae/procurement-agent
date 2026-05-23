from app.models import Vendor
from app.tools.vendor_tools import search_vendors


def test_vendor_search_returns_active_category_matches(db_session):
    db_session.add_all(
        [
            Vendor(CompanyName="A", Category="IT Hardware", Department="IT", Email="a@example.com", Rating=4.0, IsActive=True),
            Vendor(CompanyName="B", Category="IT Hardware", Department="IT", Email="b@example.com", Rating=5.0, IsActive=False),
            Vendor(CompanyName="C", Category="Office", Department="Ops", Email="c@example.com", Rating=5.0, IsActive=True),
        ]
    )
    db_session.commit()

    vendors = search_vendors(db_session, "IT Hardware", "IT")

    assert [vendor.CompanyName for vendor in vendors] == ["A"]
