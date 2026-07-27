from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int

    filename: str

    original_filename: str

    file_type: str

    file_path: str

    file_size: int

    contract_id: int

    uploaded_by: int

    uploaded_at: datetime

    #
    # AI Processing
    #

    ai_status: str

    text_content: Optional[str] = None

    summary: Optional[str] = None

    processing_started_at: Optional[datetime] = None

    processing_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True