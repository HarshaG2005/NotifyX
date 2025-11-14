from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import notifications,users,auth
from prometheus_client import generate_latest, CollectorRegistry, REGISTRY
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# Create tables
#models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NotifyX",  
    description="Multi-channel notification infrastructure",
    version="1.0.0"
)
#  ADD RATE LIMITER
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# CORS Middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers

app.include_router(notifications.router)
app.include_router(users.router)
app.include_router(auth.router)
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
