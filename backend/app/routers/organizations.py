from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationCreate

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


@router.post("/")
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_organization = Organization(
        name=organization.name,
        company_type=organization.company_type,
        country=organization.country,
        industry=organization.industry,
        owner_id=current_user.id
    )

    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)

    return {
        "message": "Organization created successfully",
        "id": new_organization.id,
        "name": new_organization.name,
        "owner": current_user.email
    }


@router.get("/")
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    organizations = db.query(Organization).filter(
        Organization.owner_id == current_user.id
    ).all()

    return organizations