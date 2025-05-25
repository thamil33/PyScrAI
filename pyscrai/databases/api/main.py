"""
FastAPI application setup
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.engine import router as engine_router

app = FastAPI(
    title="PyScrAI Engine API",
    description="API for PyScrAI engine management and event processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(engine_router, tags=["engines"])

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "PyScrAI Engine API is running"
    }
