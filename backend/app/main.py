from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models_registry  # noqa: F401  (registers models with Base.metadata)
from app.common.exceptions import DomainError, NotFoundError, ValidationFailedError
from app.config import get_settings
from app.database import Base, engine
from app.modules.attendance.router import router as attendance_router
from app.modules.matches.router import router as matches_router
from app.modules.members.router import router as members_router
from app.modules.publishing.router import router as publishing_router
from app.modules.teams.router import router as teams_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience only — real deployments manage schema via Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Attendance & Team Balancer API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationFailedError)
def handle_validation_failed(request: Request, exc: ValidationFailedError):
    return JSONResponse(status_code=400, content={"detail": str(exc), "issues": exc.issues})


@app.exception_handler(DomainError)
def handle_domain_error(request: Request, exc: DomainError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(members_router)
app.include_router(matches_router)
app.include_router(attendance_router)
app.include_router(teams_router)
app.include_router(publishing_router)
