from fastapi import APIRouter

from app.scheduler.discovery_scheduler import run_discovery
from app.scheduler.scoring_scheduler import run_scoring
from app.scheduler.outreach_scheduler import run_outreach

router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
)


@router.get("/status")
def scheduler_status():

    return {
        "scheduler": "Running",
        "discovery": "Available",
        "scoring": "Available",
        "outreach": "Available",
    }


@router.post("/run/discovery")
def discovery():

    run_discovery()

    return {
        "status": "Discovery executed"
    }


@router.post("/run/scoring")
def scoring():

    run_scoring()

    return {
        "status": "Scoring executed"
    }


@router.post("/run/outreach")
def outreach():

    run_outreach()

    return {
        "status": "Outreach executed"
    }