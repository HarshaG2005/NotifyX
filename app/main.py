from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import jobs,notifications

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Scheduler",
    description="Async job queue system",
    version="1.0.0"
)

# Include routers
app.include_router(jobs.router)
app.include_router(notifications.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "Job Scheduler API", "docs": "/docs"}
