"""
UT-RIS — Radiology Information System
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base


def create_application() -> FastAPI:
    """Application factory — creates and configures the FastAPI app."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "API untuk Sistem Informasi Radiologi — Capstone Universitas Terbuka\n\n"
            "## Autentikasi\n"
            "Gunakan endpoint `POST /api/v1/auth/login` untuk mendapatkan Bearer token, "
            "lalu klik tombol **Authorize** di atas dan masukkan token.\n\n"
            "## Role & Akses\n"
            "| Role | Akses |\n"
            "|------|-------|\n"
            "| `admin` | Full access |\n"
            "| `radiolog` | Studies, Reports, read Patients/Appointments |\n"
            "| `dokter` | Read Patients/Studies/Reports, create Appointments |\n"
            "| `resepsionis` | Patients, Appointments, read Studies |"
        ),
        docs_url="/docs"   if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )

    # ─── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Security headers middleware ──────────────────────────────────
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # ─── Routers ──────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ─── Startup ──────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup():
        if settings.ENVIRONMENT == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    # ─── Health endpoints ─────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_application()
