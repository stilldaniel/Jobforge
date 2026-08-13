from fastapi import FastAPI

app = FastAPI(
    title="JobForge API",
    description="AI-powered career intelligence platform",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "jobforge-api",
    }