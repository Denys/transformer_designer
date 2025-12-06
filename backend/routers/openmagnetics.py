"""
OpenMagnetics API endpoints

Provides access to the extensive OpenMagnetics database of cores and materials.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel, Field

from integrations.openmagnetics import get_openmagnetics_db


router = APIRouter(prefix="/api/openmagnetics", tags=["openmagnetics"])


class OpenMagneticsCoreResult(BaseModel):
    """Core result from OpenMagnetics database."""
    source: str = "openmagnetics"
    name: str
    part_number: str
    manufacturer: str
    geometry: str
    material: str
    Ae_cm2: float
    Wa_cm2: float
    Ap_cm4: float
    Ve_cm3: float
    lm_cm: float
    Bsat_T: float
    datasheet_url: str = ""


class OpenMagneticsSummary(BaseModel):
    """Database summary statistics."""
    available: bool
    core_count: int = 0
    manufacturers: List[str] = []
    shape_families: List[str] = []
    material_count: int = 0
    error: Optional[str] = None


class CoreSearchQuery(BaseModel):
    """Core search parameters."""
    min_Ap_cm4: Optional[float] = Field(None, description="Minimum area product [cm⁴]")
    max_Ap_cm4: Optional[float] = Field(None, description="Maximum area product [cm⁴]")
    shape_family: Optional[str] = Field(None, description="Core shape (E, ETD, PQ, RM)")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    material: Optional[str] = Field(None, description="Material name")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")


@router.get("/status", response_model=OpenMagneticsSummary)
async def get_openmagnetics_status():
    """
    Get OpenMagnetics database status and summary statistics.
    
    Returns number of available cores, manufacturers, shapes, and materials.
    """
    db = get_openmagnetics_db()
    summary = db.get_database_summary()
    return OpenMagneticsSummary(**summary)


@router.get("/cores", response_model=List[OpenMagneticsCoreResult])
async def search_cores(
    min_Ap_cm4: Optional[float] = Query(None, description="Minimum Ap [cm⁴]"),
    max_Ap_cm4: Optional[float] = Query(None, description="Maximum Ap [cm⁴]"),
    shape_family: Optional[str] = Query(None, description="Shape (E, ETD, PQ, etc.)"),
    manufacturer: Optional[str] = Query(None, description="Manufacturer"),
    material: Optional[str] = Query(None, description="Material name"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
):
    """
    Search for cores in the OpenMagnetics database.
    
    Filter by area product range, geometry, manufacturer, and material.
    Returns cores sorted by Ap (smallest first).
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    cores = db.get_cores(
        min_Ap_cm4=min_Ap_cm4,
        max_Ap_cm4=max_Ap_cm4,
        shape_family=shape_family,
        manufacturer=manufacturer,
        material=material,
        limit=limit,
    )
    
    return [OpenMagneticsCoreResult(**c) for c in cores]


@router.get("/cores/suitable")
async def find_suitable_cores(
    required_Ap_cm4: float = Query(..., description="Required Ap [cm⁴]"),
    frequency_Hz: float = Query(..., description="Operating frequency [Hz]"),
    geometry: Optional[str] = Query(None, description="Preferred geometry"),
    material: Optional[str] = Query(None, description="Preferred material"),
    count: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """
    Find cores suitable for a given Ap requirement.
    
    Returns cores that meet the Ap requirement with reasonable margin.
    Filters by frequency suitability (ferrite for high freq, steel for low).
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    cores = db.find_suitable_cores(
        required_Ap_cm4=required_Ap_cm4,
        frequency_Hz=frequency_Hz,
        preferred_geometry=geometry,
        preferred_material=material,
        count=count,
    )
    
    return {
        "required_Ap_cm4": required_Ap_cm4,
        "frequency_Hz": frequency_Hz,
        "cores_found": len(cores),
        "cores": cores,
    }


@router.get("/manufacturers")
async def get_manufacturers():
    """Get list of available core manufacturers."""
    db = get_openmagnetics_db()
    return {
        "manufacturers": db.get_manufacturers(),
        "count": len(db.get_manufacturers()),
    }


@router.get("/shapes")
async def get_shape_families():
    """Get list of available core shape families."""
    db = get_openmagnetics_db()
    return {
        "shape_families": db.get_shape_families(),
        "count": len(db.get_shape_families()),
    }


@router.get("/materials")
async def get_materials():
    """Get list of available material names."""
    db = get_openmagnetics_db()
    return {
        "materials": db.get_material_names(),
        "count": len(db.get_material_names()),
    }
