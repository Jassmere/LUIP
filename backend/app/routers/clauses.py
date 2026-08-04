from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.clause import ClauseResponse
from app.services.clause_service import ClauseService

router = APIRouter(
    prefix="/clauses",
    tags=["Clauses"],
)


@router.get(
    "/",
    response_model=list[ClauseResponse],
)
def list_clauses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ClauseService.list_clauses(db)


@router.get(
    "/statistics",
)
def clause_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ClauseService.get_statistics(db)


@router.get(
    "/high-risk",
    response_model=list[ClauseResponse],
)
def high_risk_clauses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ClauseService.get_high_risk_clauses(db)


@router.get(
    "/document/{document_id}",
    response_model=list[ClauseResponse],
)
def get_document_clauses(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ClauseService.get_document_clauses(
        db,
        document_id,
    )


@router.get(
    "/{clause_id}",
    response_model=ClauseResponse,
)
def get_clause(
    clause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    clause = ClauseService.get_clause(
        db,
        clause_id,
    )

    if clause is None:
        raise HTTPException(
            status_code=404,
            detail="Clause not found.",
        )

    return clause