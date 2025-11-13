from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import jobs,notifications,users
from prometheus_client import generate_latest, CollectorRegistry, REGISTRY
from fastapi.responses import Response


# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NotifyX",  
    description="Multi-channel notification infrastructure",
    version="1.0.0"
)

# Include routers
app.include_router(jobs.router)
app.include_router(notifications.router)
app.include_router(users.router)
@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(REGISTRY), media_type="text/plain")
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"service": "NotifyX",
        "version": "1.0.0",
        "docs": "/docs"}
