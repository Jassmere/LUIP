from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_type: str
    file_path: str
    contract_id: int


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_path: str
    uploaded_at: datetime
    contract_id: int
    uploaded_by: int

    class Config:
        from_attributes = True