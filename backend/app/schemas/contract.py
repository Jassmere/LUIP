from datetime import date
from typing import Optional

from pydantic import BaseModel


class ContractCreate(BaseModel):
    title: str
    contract_type: str
    counterparty: str
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    organization_id: int


class ContractResponse(BaseModel):
    id: int
    title: str
    contract_type: str
    status: str
    counterparty: str
    effective_date: Optional[date]
    expiry_date: Optional[date]
    organization_id: int
    created_by: int

    class Config:
        from_attributes = True