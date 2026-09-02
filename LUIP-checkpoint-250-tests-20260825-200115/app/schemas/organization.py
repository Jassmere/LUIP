from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    company_type: str
    country: str
    industry: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    company_type: str
    country: str
    industry: str
    owner_id: int

    class Config:
        from_attributes = True