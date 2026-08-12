from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_database
from app.diagnostics.diagnostics_engine import DiagnosticsEngine

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

from app.routers.health import router as health_router
from app.routers.users import router as users_router
from app.routers.organizations import router as organizations_router
from app.routers.contracts import router as contracts_router
from app.routers.documents import router as documents_router
from app.routers.clauses import router as clauses_router
from app.routers.vega import router as vega_router
from app.routers.diagnostics import router as diagnostics_router
from app.routers.discovery import router as discovery_router
from app.routers.buying_intelligence import router as buying_router
from app.routers.buying_signals import router as buying_signals_router
from app.routers.scheduler import router as scheduler_router

# ---------------------------------------------------------
# Scheduler
# ---------------------------------------------------------

from app.scheduler.scheduler import Scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):

    # -----------------------------------------------------
    # Create database tables
    # -----------------------------------------------------

    create_database()

    # -----------------------------------------------------
    # Diagnostics startup
    # -----------------------------------------------------

    DiagnosticsEngine.startup()

    # -----------------------------------------------------
    # Start background scheduler
    # -----------------------------------------------------

    Scheduler.start()

    yield

    # -----------------------------------------------------
    # Shutdown scheduler
    # -----------------------------------------------------

    Scheduler.shutdown()


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="LUIP Enterprise Platform",
    version="1.1.1",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# Register Routers
# ---------------------------------------------------------

app.include_router(health_router)

app.include_router(users_router)

app.include_router(organizations_router)

app.include_router(contracts_router)

app.include_router(documents_router)

app.include_router(clauses_router)

app.include_router(vega_router)

app.include_router(diagnostics_router)

app.include_router(discovery_router)

app.include_router(buying_router)

app.include_router(buying_signals_router)

app.include_router(scheduler_router)


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "platform": "LUIP Enterprise Platform",
        "version": "1.1.1",
        "status": "Running",
    }