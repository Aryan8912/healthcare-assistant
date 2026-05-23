"""
main.py — FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.database import init_db
from backend.db.seed import seed

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting MedAssist AI Backend...")
    await init_db()
    await seed()
    logger.info("✅ Startup complete.")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="MedAssist AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = ["*"] if settings.app_env == "development" else settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = False,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

from backend.api.chat         import router as chat_router
from backend.api.appointments import router as appt_router
from backend.api.documents    import router as docs_router

app.include_router(chat_router,  prefix="/api", tags=["Chat"])
app.include_router(appt_router,  prefix="/api", tags=["Appointments"])
app.include_router(docs_router,  prefix="/api", tags=["Documents"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "MedAssist AI Backend", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)