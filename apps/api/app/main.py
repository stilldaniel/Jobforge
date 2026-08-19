from fastapi import FastAPI
from app.api.career_profiles import router as career_profiles_router
from app.api.users import router as users_router
from app.api.jobs import router as jobs_router
from app.api.job_discovery import router as job_discovery_router

app = FastAPI(
    title="JobForge API",
)


app.include_router(users_router)
app.include_router(career_profiles_router)
app.include_router(jobs_router)
app.include_router(job_discovery_router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jobforge-api",
    }