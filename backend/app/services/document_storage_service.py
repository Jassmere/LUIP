from datetime import datetime

from sqlalchemy.orm import Session

from app.models.clause import Clause
from app.models.document import Document
from app.services.clause_extraction_service import ClauseExtractionService
from app.services.document_ai_service import DocumentAIService
from app.services.text_extraction_service import TextExtractionService
from app.storage.storage_service import StorageService


class DocumentService:
    """
    Handles all document business logic.

    Responsibilities:
    - Store uploaded files
    - Extract document text
    - Generate AI summaries
    - Extract legal clauses
    - Save clause intelligence
    - Create database records
    """

    @staticmethod
    async def create_document(
        db: Session,
        upload_file,
        contract_id: int,
        uploaded_by: int,
    ) -> Document:

        (
            stored_filename,
            file_path,
            file_size,
            checksum,
        ) = await StorageService.save_file(upload_file)

        ai_status = "Completed"

        text_content = ""

        summary = None

        processing_started_at = datetime.utcnow()

        try:

            text_content = TextExtractionService.extract_text(
                file_path
            )

            summary = DocumentAIService.generate_summary(
                text_content
            )

        except Exception:

            ai_status = "Failed"

        processing_completed_at = datetime.utcnow()

        document = Document(

            filename=stored_filename,

            original_filename=upload_file.filename,

            file_type=upload_file.content_type,

            file_path=file_path,

            file_size=file_size,

            checksum=checksum,

            version=1,

            contract_id=contract_id,

            uploaded_by=uploaded_by,

            uploaded_at=datetime.utcnow(),

            ai_status=ai_status,

            text_content=text_content,

            summary=summary,

            processing_started_at=processing_started_at,

            processing_completed_at=processing_completed_at,

        )

        db.add(document)

        db.commit()

        db.refresh(document)

        #
        # ------------------------------------
        # Extract and Save Clauses
        # ------------------------------------
        #

        clauses = ClauseExtractionService.extract(
            text_content
        )

        for clause_data in clauses:

            clause = Clause(

                document_id=document.id,

                clause_type=clause_data["clause_type"],

                heading=clause_data["heading"],

                content=clause_data["content"],

                confidence_score=clause_data["confidence_score"],

                page_number=None,

                created_at=datetime.utcnow(),

            )

            db.add(clause)

        db.commit()

        return document

    @staticmethod
    def get_document(
        db: Session,
        document_id: int,
    ):

        return (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    @staticmethod
    def list_documents(
        db: Session,
    ):

        return (
            db.query(Document)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

    @staticmethod
    def delete_document(
        db: Session,
        document: Document,
    ):

        db.delete(document)

        db.commit()