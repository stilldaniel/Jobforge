from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.career_profiles import router as career_profiles_router
from app.api.users import router as users_router
from app.api.jobs import router as jobs_router
from app.api.job_discovery import router as job_discovery_router
from app.api.matches import router as matches_router
from app.api.notifications import router as notifications_router
from app.services.scheduler import start_scheduler, stop_scheduler
from app.api.saved_jobs import router as saved_jobs_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="JobForge API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users_router)
app.include_router(career_profiles_router)
app.include_router(jobs_router)
app.include_router(job_discovery_router)
app.include_router(matches_router)
app.include_router(notifications_router)
app.include_router(saved_jobs_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jobforge-api",
    }