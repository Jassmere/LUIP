from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.contract import Contract
from app.models.organization import Organization
from app.models.user import User
from app.schemas.contract import ContractCreate

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"]
)


@router.post("/")
def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    organization = db.query(Organization).filter(
        Organization.id == contract.organization_id,
        Organization.owner_id == current_user.id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    new_contract = Contract(
        title=contract.title,
        contract_type=contract.contract_type,
        status="Draft",
        counterparty=contract.counterparty,
        effective_date=contract.effective_date,
        expiry_date=contract.expiry_date,
        organization_id=contract.organization_id,
        created_by=current_user.id
    )

    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    return {
        "message": "Contract created successfully",
        "id": new_contract.id,
        "title": new_contract.title,
        "status": new_contract.status
    }


@router.get("/")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    contracts = (
        db.query(Contract)
        .filter(Contract.created_by == current_user.id)
        .all()
    )

    return contracts