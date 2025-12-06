"""
Power Transformer Designer API
FastAPI backend implementing McLyman's Ap/Kg methodology
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import transformer, inductor, openmagnetics

app = FastAPI(
    title="Power Transformer Designer",
    description="Design transformers and inductors using McLyman's Area Product (Ap) and Core Geometry (Kg) methods. Now with OpenMagnetics database access!",
    version="0.2.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transformer.router)
app.include_router(inductor.router)
app.include_router(openmagnetics.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.2.0"}


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Power Transformer Designer API",
        "version": "0.2.0",
        "docs": "/docs",
        "endpoints": {
            "transformer_design": "/api/design/transformer",
            "inductor_design": "/api/design/inductor",
            "cores": "/api/cores",
            "materials": "/api/materials",
            "openmagnetics": "/api/openmagnetics",
        }
    }
