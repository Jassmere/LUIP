from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.clause import Clause
from app.schemas.clause import ClauseResponse

router = APIRouter(
    prefix="/clauses",
    tags=["Clauses"],
)


@router.get(
    "/document/{document_id}",
    response_model=list[ClauseResponse],
)
def get_document_clauses(
    document_id: int,
    db: Session = Depends(get_db),
):

    clauses = (
        db.query(Clause)
        .filter(
            Clause.document_id == document_id
        )
        .order_by(Clause.id)
        .all()
    )

    return clauses


@router.get(
    "/{clause_id}",
    response_model=ClauseResponse,
)
def get_clause(
    clause_id: int,
    db: Session = Depends(get_db),
):

    clause = (
        db.query(Clause)
        .filter(
            Clause.id == clause_id
        )
        .first()
    )

    if clause is None:

        raise HTTPException(
            status_code=404,
            detail="Clause not found",
        )

    return clause