"""
Main API v1 router — aggregates all feature routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, patients, appointments, studies, reports, dashboard

api_router = APIRouter()

api_router.include_router(auth.router,         prefix="/auth",         tags=["Authentication"])
api_router.include_router(users.router,        prefix="/users",        tags=["Users"])
api_router.include_router(patients.router,     prefix="/patients",     tags=["Patients"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(studies.router,      prefix="/studies",      tags=["Studies"])
api_router.include_router(reports.router,      prefix="/reports",      tags=["Reports"])
api_router.include_router(dashboard.router,    prefix="/dashboard",    tags=["Dashboard"])
