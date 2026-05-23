import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.api import approvals, auth, logs, requests, vendors
from app.config import get_settings
from app.database import engine, init_db
from app.exceptions import ProcurementError


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token"],
)

app.include_router(requests.router)
app.include_router(approvals.router)
app.include_router(vendors.router)
app.include_router(logs.router)
app.include_router(auth.router)


@app.exception_handler(ProcurementError)
async def procurement_exception_handler(_: Request, exc: ProcurementError) -> JSONResponse:
    logging.getLogger(__name__).warning("handled_error=%s message=%s", exc.__class__.__name__, exc.user_message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.user_message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("unhandled_error=%s", exc.__class__.__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logging.getLogger(__name__).warning("database_health_check_failed=%s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database health check failed") from exc
    return {"status": "ok", "database": "ok"}
