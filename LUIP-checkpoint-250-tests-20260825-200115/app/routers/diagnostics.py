from fastapi import APIRouter

from app.diagnostics.diagnostics_engine import DiagnosticsEngine

router = APIRouter(
    prefix="/diagnostics",
    tags=["Diagnostics"],
)


@router.get("/status")
def diagnostics_status():

    return DiagnosticsEngine.run()