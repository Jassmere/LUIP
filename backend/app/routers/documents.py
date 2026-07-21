from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.contract import Contract
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/")
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    contract = (
        db.query(Contract)
        .filter(
            Contract.id == document.contract_id,
            Contract.created_by == current_user.id
        )
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found"
        )

    new_document = Document(
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_path=document.file_path,
        contract_id=document.contract_id,
        uploaded_by=current_user.id
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "message": "Document created successfully",
        "id": new_document.id,
        "filename": new_document.filename
    }


@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    documents = (
        db.query(Document)
        .filter(Document.uploaded_by == current_user.id)
        .all()
    )

    return documents