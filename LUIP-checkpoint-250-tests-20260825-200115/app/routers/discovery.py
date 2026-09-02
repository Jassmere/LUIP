"""
LUIP Discovery API Router.

Provides API endpoints for:

1. Manual company discovery
2. Company discovery + preparation
3. Company scanning
4. Discovery + scanning
5. Company discovery status
6. Discovery Engine status

Version: 1.0.9
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.discovery.discovery_engine import DiscoveryEngine


router = APIRouter(
    prefix="/discovery",
    tags=["Company Discovery"],
)


# ---------------------------------------------------------
# DISCOVER COMPANY
# ---------------------------------------------------------

@router.post("/company")
def discover_company(
    name: str,
    website: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    city: str | None = None,
    source: str = "Manual",
    db: Session = Depends(get_db),
):
    """
    Discover a company and store it in LUIP.

    Existing companies are returned instead of creating
    duplicate records.
    """

    company = DiscoveryEngine.discover_company(
        db=db,
        name=name,
        website=website,
        industry=industry,
        country=country,
        city=city,
        source=source,
    )

    if company is None:
        raise HTTPException(
            status_code=400,
            detail="Company name is required.",
        )

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company_id": company.id,
        "company": company.name,
        "website": company.website,
        "industry": company.industry,
        "country": company.country,
        "city": company.city,
        "discovered_from": company.discovered_from,
        "scan_status": company.scan_status,
        "message": "Company discovered successfully.",
    }


# ---------------------------------------------------------
# DISCOVER AND PREPARE COMPANY
# ---------------------------------------------------------

@router.post("/company/prepare")
def discover_and_prepare_company(
    name: str,
    website: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    city: str | None = None,
    source: str = "Manual",
    db: Session = Depends(get_db),
):
    """
    Discover a company and prepare it for scanning.

    Lifecycle:

        Discovery
            ↓
        Pending
            ↓
        Ready for Scan
    """

    company = DiscoveryEngine.discover_and_prepare(
        db=db,
        name=name,
        website=website,
        industry=industry,
        country=country,
        city=city,
        source=source,
    )

    if company is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to discover company.",
        )

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company_id": company.id,
        "company": company.name,
        "website": company.website,
        "industry": company.industry,
        "country": company.country,
        "city": company.city,
        "discovered_from": company.discovered_from,
        "scan_status": company.scan_status,
        "message": "Company discovered and prepared for scanning.",
    }


# ---------------------------------------------------------
# SCAN EXISTING COMPANY
# ---------------------------------------------------------

@router.post("/company/{company_id}/scan")
def scan_company(
    company_id: int,
    linkedin_url: str | None = None,
    linkedin_provider: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Execute the Discovery Engine scanner pipeline
    against an existing company.

    Currently active scanners:

        1. Website Scanner
        2. LinkedIn Scanner

    Future scanners:

        3. News Scanner
        4. Procurement Scanner
        5. Technology Scanner
    """

    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company {company_id} not found.",
        )

    result = DiscoveryEngine.scan_company(
        db=db,
        company=company,
        linkedin_url=linkedin_url,
        linkedin_provider=linkedin_provider,
    )

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to scan company.",
        )

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company": {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "linkedin_url": company.linkedin_url,
            "industry": company.industry,
            "country": company.country,
            "city": company.city,
            "scan_status": company.scan_status,
            "last_scan": company.last_scan,
        },
        "website": result.get("website"),
        "linkedin": result.get("linkedin"),
        "message": "Company discovery scan completed successfully.",
    }


# ---------------------------------------------------------
# DISCOVER AND SCAN
# ---------------------------------------------------------

@router.post("/company/discover-and-scan")
def discover_and_scan_company(
    name: str,
    website: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    city: str | None = None,
    source: str = "Manual",
    linkedin_url: str | None = None,
    linkedin_provider: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Discover a company and immediately execute the
    Discovery Engine scanner pipeline.

    Lifecycle:

        Company Discovery
                ↓
        Discovery Engine
                ↓
        Website Scanner
                ↓
        LinkedIn Scanner
                ↓
        Scan Completed
    """

    result = DiscoveryEngine.discover_and_scan(
        db=db,
        name=name,
        website=website,
        industry=industry,
        country=country,
        city=city,
        source=source,
        linkedin_url=linkedin_url,
        linkedin_provider=linkedin_provider,
    )

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to discover and scan company.",
        )

    company = result.get("company")

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company": {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "linkedin_url": company.linkedin_url,
            "industry": company.industry,
            "country": company.country,
            "city": company.city,
            "discovered_from": company.discovered_from,
            "scan_status": company.scan_status,
            "last_scan": company.last_scan,
        },
        "website": result.get("website"),
        "linkedin": result.get("linkedin"),
        "message": "Company discovered and scanned successfully.",
    }


# ---------------------------------------------------------
# GET COMPANY
# ---------------------------------------------------------

@router.get("/company/{company_id}")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the complete discovery profile for a company.
    """

    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company {company_id} not found.",
        )

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company": {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "linkedin_url": company.linkedin_url,
            "industry": company.industry,
            "country": company.country,
            "city": company.city,
            "company_size": company.company_size,
            "description": company.description,
            "discovered_from": company.discovered_from,
            "discovery_date": company.discovery_date,
            "scan_status": company.scan_status,
            "last_scan": company.last_scan,
            "active": company.active,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
        },
    }


# ---------------------------------------------------------
# GET COMPANY SCAN STATUS
# ---------------------------------------------------------

@router.get("/company/{company_id}/status")
def get_company_scan_status(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the current Discovery Engine scan status
    for a company.
    """

    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company {company_id} not found.",
        )

    return {
        "success": True,
        "version": DiscoveryEngine.VERSION,
        "company_id": company.id,
        "company": company.name,
        "scan_status": company.scan_status,
        "last_scan": company.last_scan,
        "active": company.active,
    }


# ---------------------------------------------------------
# DISCOVERY ENGINE STATUS
# ---------------------------------------------------------

@router.get("/status")
def discovery_status():
    """
    Return Discovery Engine status information.
    """

    return DiscoveryEngine.status()