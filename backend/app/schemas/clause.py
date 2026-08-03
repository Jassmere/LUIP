from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClauseResponse(BaseModel):

    id: int

    document_id: int

    clause_type: str

    heading: str

    content: str

    confidence_score: float

    page_number: int | None = None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )