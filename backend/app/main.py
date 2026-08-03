from fastapi import FastAPI

from app.database import create_database

from app.routers.health import router as health_router
from app.routers.users import router as users_router
from app.routers.organizations import router as organizations_router
from app.routers.contracts import router as contracts_router
from app.routers.documents import router as documents_router
from app.routers.clauses import router as clauses_router


app = FastAPI(
    title="LUIP API",
    version="1.0.0",
)


@app.on_event("startup")
def startup():

    create_database()


app.include_router(health_router)

app.include_router(users_router)

app.include_router(organizations_router)

app.include_router(contracts_router)

app.include_router(documents_router)

app.include_router(clauses_router)