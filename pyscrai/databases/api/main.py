"""
FastAPI application setup
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



from .routes.engine_endpoint import router as engine_router
from .routes.scenarios_endpoint import router as scenarios_router
from .routes.templates_endpoint import router as templates_router
from .routes.runner_endpoint import router as runner_router

app = FastAPI(
    title="PyScrAI Engine API",
    description="API for PyScrAI engine management and event processing",
    version="0.1.0"
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

app.include_router(engine_router)
app.include_router(scenarios_router)
app.include_router(templates_router)
app.include_router(runner_router)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "PyScrAI Engine API is running"
    }
