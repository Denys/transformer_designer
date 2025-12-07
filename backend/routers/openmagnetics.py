"""
OpenMagnetics API endpoints

Provides access to the extensive OpenMagnetics database of cores and materials.

Enhanced Features:
- Loss-based core filtering
- Material property lookup
- Core comparison by loss
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from integrations.openmagnetics import get_openmagnetics_db


router = APIRouter(prefix="/api/openmagnetics", tags=["openmagnetics"])


# ============================================================================
# Response Models
# ============================================================================

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
    MLT_cm: float = 0
    At_cm2: float = 0
    weight_g: float = 0
    Bsat_T: float
    mu_i: float = 2000
    datasheet_url: str = ""


class CoreWithLossResult(OpenMagneticsCoreResult):
    """Core result with loss calculations."""
    estimated_core_loss_W: Optional[float] = None
    loss_density_kW_m3: Optional[float] = None
    loss_density_mW_cm3: Optional[float] = None
    steinmetz_k: Optional[float] = None
    steinmetz_alpha: Optional[float] = None
    steinmetz_beta: Optional[float] = None
    at_frequency_kHz: Optional[float] = None
    at_Bac_T: Optional[float] = None
    at_temperature_C: Optional[float] = None


class MaterialPropertiesResult(BaseModel):
    """Material properties response."""
    name: str
    family: str
    initial_permeability: float
    saturation_flux_T: float
    curie_temp_C: float
    resistivity_ohm_m: float
    density_kg_m3: float
    steinmetz_k: float
    steinmetz_alpha: float
    steinmetz_beta: float
    loss_reference_freq_Hz: float
    loss_reference_B_T: float
    loss_reference_kW_m3: float
    temperature_coefficients: Dict[str, float]


class CoreLossCalculation(BaseModel):
    """Core loss calculation result."""
    core_loss_W: float
    loss_density_mW_cm3: float
    loss_density_kW_m3: float
    steinmetz_k: float
    steinmetz_alpha: float
    steinmetz_beta: float
    temperature_C: float
    frequency_Hz: float
    Bac_T: float
    method: str


class OpenMagneticsSummary(BaseModel):
    """Database summary statistics."""
    available: bool
    core_count: int = 0
    manufacturers: List[str] = []
    shape_families: List[str] = []
    material_count: int = 0
    error: Optional[str] = None


# ============================================================================
# Request Models
# ============================================================================

class CoreSearchQuery(BaseModel):
    """Core search parameters."""
    min_Ap_cm4: Optional[float] = Field(None, description="Minimum area product [cm⁴]")
    max_Ap_cm4: Optional[float] = Field(None, description="Maximum area product [cm⁴]")
    shape_family: Optional[str] = Field(None, description="Core shape (E, ETD, PQ, RM)")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    material: Optional[str] = Field(None, description="Material name")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")


class LossBasedSearchQuery(BaseModel):
    """Loss-based core search parameters."""
    required_Ap_cm4: float = Field(..., description="Required area product [cm⁴]")
    frequency_Hz: float = Field(..., description="Operating frequency [Hz]")
    Bac_T: float = Field(..., description="AC flux density [T peak]")
    max_core_loss_W: Optional[float] = Field(None, description="Maximum core loss [W]")
    max_loss_density_kW_m3: Optional[float] = Field(None, description="Maximum loss density [kW/m³]")
    temperature_C: float = Field(100, description="Operating temperature [°C]")
    preferred_geometry: Optional[str] = Field(None, description="Preferred core shape")
    preferred_material: Optional[str] = Field(None, description="Preferred material")
    count: int = Field(10, ge=1, le=50, description="Number of results")


class CoreLossRequest(BaseModel):
    """Core loss calculation request."""
    core_name: str = Field(..., description="Core name from database")
    frequency_Hz: float = Field(..., description="Operating frequency [Hz]")
    Bac_T: float = Field(..., description="AC flux density [T peak]")
    temperature_C: float = Field(100, description="Operating temperature [°C]")
    waveform: str = Field("sinusoidal", description="Waveform type")


# ============================================================================
# Endpoints
# ============================================================================


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


@router.post("/cores/search-by-loss", response_model=Dict[str, Any])
async def search_cores_by_loss(query: LossBasedSearchQuery):
    """
    Search for cores filtered by loss requirements.
    
    This endpoint finds cores that meet both Ap and core loss requirements.
    Results are sorted by estimated core loss (lowest first), enabling
    selection of the most efficient core for the application.
    
    Use this for:
    - High-frequency designs where core loss dominates
    - Efficiency-critical applications
    - Thermal-limited designs
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    cores = db.find_cores_by_loss(
        required_Ap_cm4=query.required_Ap_cm4,
        frequency_Hz=query.frequency_Hz,
        Bac_T=query.Bac_T,
        max_core_loss_W=query.max_core_loss_W,
        max_loss_density_kW_m3=query.max_loss_density_kW_m3,
        temperature_C=query.temperature_C,
        preferred_geometry=query.preferred_geometry,
        preferred_material=query.preferred_material,
        count=query.count,
    )
    
    return {
        "query": {
            "required_Ap_cm4": query.required_Ap_cm4,
            "frequency_Hz": query.frequency_Hz,
            "Bac_T": query.Bac_T,
            "temperature_C": query.temperature_C,
            "max_core_loss_W": query.max_core_loss_W,
            "max_loss_density_kW_m3": query.max_loss_density_kW_m3,
        },
        "cores_found": len(cores),
        "cores": cores,
    }


@router.get("/cores/by-loss")
async def find_cores_by_loss(
    required_Ap_cm4: float = Query(..., description="Required Ap [cm⁴]"),
    frequency_Hz: float = Query(..., description="Operating frequency [Hz]"),
    Bac_T: float = Query(..., description="AC flux density [T]"),
    max_core_loss_W: Optional[float] = Query(None, description="Max core loss [W]"),
    max_loss_density_kW_m3: Optional[float] = Query(None, description="Max loss density [kW/m³]"),
    temperature_C: float = Query(100, description="Temperature [°C]"),
    geometry: Optional[str] = Query(None, description="Preferred geometry"),
    material: Optional[str] = Query(None, description="Preferred material"),
    count: int = Query(10, ge=1, le=50, description="Number of results"),
):
    """
    Find cores sorted by core loss (GET version for simple queries).
    
    Returns cores that meet Ap requirements, sorted by estimated core loss.
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    cores = db.find_cores_by_loss(
        required_Ap_cm4=required_Ap_cm4,
        frequency_Hz=frequency_Hz,
        Bac_T=Bac_T,
        max_core_loss_W=max_core_loss_W,
        max_loss_density_kW_m3=max_loss_density_kW_m3,
        temperature_C=temperature_C,
        preferred_geometry=geometry,
        preferred_material=material,
        count=count,
    )
    
    return {
        "required_Ap_cm4": required_Ap_cm4,
        "frequency_Hz": frequency_Hz,
        "Bac_T": Bac_T,
        "cores_found": len(cores),
        "cores": cores,
    }


@router.post("/cores/calculate-loss", response_model=CoreLossCalculation)
async def calculate_core_loss(request: CoreLossRequest):
    """
    Calculate core loss for a specific core.
    
    Calculates Steinmetz equation loss with temperature and waveform corrections.
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    # Find the core
    cores = db.get_cores(limit=500)
    matching = [c for c in cores if c.get('name', '') == request.core_name]
    
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"Core '{request.core_name}' not found"
        )
    
    core = matching[0]
    result = db.calculate_core_loss_detailed(
        core=core,
        frequency_Hz=request.frequency_Hz,
        Bac_T=request.Bac_T,
        temperature_C=request.temperature_C,
        waveform=request.waveform,
    )
    
    return CoreLossCalculation(
        core_loss_W=result.core_loss_W,
        loss_density_mW_cm3=result.loss_density_mW_cm3,
        loss_density_kW_m3=result.loss_density_kW_m3,
        steinmetz_k=result.steinmetz_k,
        steinmetz_alpha=result.steinmetz_alpha,
        steinmetz_beta=result.steinmetz_beta,
        temperature_C=result.temperature_C,
        frequency_Hz=result.frequency_Hz,
        Bac_T=result.Bac_T,
        method=result.method,
    )


@router.get("/materials/{material_name}", response_model=MaterialPropertiesResult)
async def get_material_properties(material_name: str):
    """
    Get detailed properties for a specific material.
    
    Returns Steinmetz coefficients, permeability, saturation, and other properties.
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    props = db.get_material_properties(material_name)
    
    if props is None:
        raise HTTPException(
            status_code=404,
            detail=f"Material '{material_name}' not found"
        )
    
    return MaterialPropertiesResult(
        name=props.name,
        family=props.family,
        initial_permeability=props.initial_permeability,
        saturation_flux_T=props.saturation_flux_T,
        curie_temp_C=props.curie_temp_C,
        resistivity_ohm_m=props.resistivity_ohm_m,
        density_kg_m3=props.density_kg_m3,
        steinmetz_k=props.steinmetz_k,
        steinmetz_alpha=props.steinmetz_alpha,
        steinmetz_beta=props.steinmetz_beta,
        loss_reference_freq_Hz=props.loss_reference_freq_Hz,
        loss_reference_B_T=props.loss_reference_B_T,
        loss_reference_kW_m3=props.loss_reference_kW_m3,
        temperature_coefficients=props.temperature_coefficients,
    )


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


@router.post("/cores/compare")
async def compare_cores(
    core_names: List[str],
    frequency_Hz: float = Query(..., description="Operating frequency [Hz]"),
    Bac_T: float = Query(..., description="AC flux density [T]"),
    temperature_C: float = Query(100, description="Temperature [°C]"),
):
    """
    Compare multiple cores by their loss performance.
    
    Takes a list of core names and returns them with loss calculations,
    sorted by core loss (lowest first).
    """
    db = get_openmagnetics_db()
    
    if not db.is_available:
        raise HTTPException(
            status_code=503,
            detail="OpenMagnetics database not available"
        )
    
    # Find all matching cores
    all_cores = db.get_cores(limit=1000)
    cores_to_compare = []
    not_found = []
    
    for name in core_names:
        matching = [c for c in all_cores if c.get('name', '') == name]
        if matching:
            cores_to_compare.append(matching[0])
        else:
            not_found.append(name)
    
    if not cores_to_compare:
        raise HTTPException(
            status_code=404,
            detail=f"No cores found. Not found: {not_found}"
        )
    
    # Compare by loss
    results = db.compare_cores_by_loss(
        cores=cores_to_compare,
        frequency_Hz=frequency_Hz,
        Bac_T=Bac_T,
        temperature_C=temperature_C,
    )
    
    return {
        "frequency_Hz": frequency_Hz,
        "Bac_T": Bac_T,
        "temperature_C": temperature_C,
        "cores_compared": len(results),
        "not_found": not_found,
        "results": results,
    }
