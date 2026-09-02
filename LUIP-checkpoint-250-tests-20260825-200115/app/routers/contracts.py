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


@router.get("/{contract_id}")
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    contract = (
        db.query(Contract)
        .filter(
            Contract.id == contract_id,
            Contract.created_by == current_user.id
        )
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )

    return contract


@router.put("/{contract_id}")
def update_contract(
    contract_id: int,
    updated_contract: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    contract = (
        db.query(Contract)
        .filter(
            Contract.id == contract_id,
            Contract.created_by == current_user.id
        )
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )

    organization = (
        db.query(Organization)
        .filter(
            Organization.id == updated_contract.organization_id,
            Organization.owner_id == current_user.id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    contract.title = updated_contract.title
    contract.contract_type = updated_contract.contract_type
    contract.counterparty = updated_contract.counterparty
    contract.effective_date = updated_contract.effective_date
    contract.expiry_date = updated_contract.expiry_date
    contract.organization_id = updated_contract.organization_id

    db.commit()
    db.refresh(contract)

    return contract


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    contract = (
        db.query(Contract)
        .filter(
            Contract.id == contract_id,
            Contract.created_by == current_user.id
        )
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )

    db.delete(contract)
    db.commit()

    return {
        "message": "Contract deleted successfully"
    }