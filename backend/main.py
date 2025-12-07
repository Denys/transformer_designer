"""
Power Transformer Designer API
FastAPI backend implementing McLyman's Ap/Kg methodology

Features:
- McLyman's Area Product (Ap) and Core Geometry (Kg) methods
- Erickson's Kgfe loss-optimized design
- OpenMagnetics database integration (10,000+ cores)
- MAS export for FEA tools
- Cross-validation and confidence scoring
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import transformer, inductor, openmagnetics, export, pulse_transformer

app = FastAPI(
    title="Power Transformer Designer",
    description="""
Design transformers and inductors using McLyman's Area Product (Ap) and Core Geometry (Kg) methods.

## Features
- **McLyman's Ap Method**: Classic area product approach for initial sizing
- **McLyman's Kg Method**: Core geometry method for optimized designs
- **Erickson's Kgfe Method**: Loss-optimized design for high-frequency applications
- **OpenMagnetics Integration**: Access to 10,000+ cores from major manufacturers
- **Loss-Based Core Selection**: Find cores optimized for minimum loss
- **MAS Export**: Export designs to OpenMagnetics format for FEA tools
- **FEMM Export**: Generate Lua scripts for FEMM simulation
- **Cross-Validation**: Confidence scoring against theoretical models

## Design Methods
1. **ap_mclyman**: Classic area product - simple, reliable
2. **kg_mclyman**: Core geometry - better for high power
3. **kgfe_erickson**: Loss-optimized - best for HF efficiency

## Export Formats
- MAS JSON (OpenMagnetics compatible)
- FEMM Lua scripts
- Design JSON for archival
""",
    version="0.3.0",
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
app.include_router(export.router)
app.include_router(pulse_transformer.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.3.0"}


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Power Transformer Designer API",
        "version": "0.3.0",
        "docs": "/docs",
        "endpoints": {
            "transformer_design": "/api/design/transformer",
            "inductor_design": "/api/design/inductor",
            "pulse_transformer": "/api/design/pulse",
            "cores": "/api/cores",
            "materials": "/api/materials",
            "openmagnetics": "/api/openmagnetics",
            "export": "/api/export",
        }
    }
