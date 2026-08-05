from fastapi import APIRouter, HTTPException

from app.services.vega_review_service import VegaReviewService


router = APIRouter(

    prefix="/vega",

    tags=["Vega AI"],

)


@router.get(
    "/review/{document_id}"
)
def review_document(
    document_id: int,
):

    try:

        result = VegaReviewService.review_document(
            document_id
        )

        return result

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )