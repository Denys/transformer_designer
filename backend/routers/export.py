"""
Export API endpoints

Provides export functionality for transformer and inductor designs
to various formats:
- MAS (Magnetic Agnostic Structure) JSON
- FEMM Lua scripts
- PDF reports (future)
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import json

from integrations.mas_exporter import (
    MASExporter,
    FEMMExporter,
    export_design_to_mas,
    export_design_to_femm,
)


router = APIRouter(prefix="/api/export", tags=["export"])


# ============================================================================
# Request Models
# ============================================================================

class TransformerExportRequest(BaseModel):
    """Request model for transformer design export."""
    
    # Design result (from /api/design/transformer response)
    design_result: Dict[str, Any] = Field(..., description="Complete design result")
    
    # Original requirements
    requirements: Dict[str, Any] = Field(..., description="Design requirements")
    
    # Export options
    pretty: bool = Field(True, description="Pretty-print JSON output")
    include_metadata: bool = Field(True, description="Include export metadata")


class ExportOptions(BaseModel):
    """General export options."""
    format: str = Field("mas", description="Export format: mas, femm, pdf")
    pretty: bool = Field(True, description="Pretty-print output")
    filename: Optional[str] = Field(None, description="Suggested filename")


# ============================================================================
# Response Models
# ============================================================================

class MASExportResponse(BaseModel):
    """Response containing MAS JSON export."""
    format: str = "mas"
    version: str
    filename: str
    content: Dict[str, Any]


class FEMMExportResponse(BaseModel):
    """Response containing FEMM Lua script."""
    format: str = "femm"
    filename: str
    content: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/mas", response_model=MASExportResponse)
async def export_to_mas(request: TransformerExportRequest):
    """
    Export transformer design to MAS (Magnetic Agnostic Structure) format.
    
    MAS is the OpenMagnetics JSON format for magnetic component specifications.
    It can be used with:
    - OpenMagnetics online tools
    - FEMM (via conversion)
    - COMSOL, Ansys imports
    - Other FEA and design tools
    
    Returns the complete MAS document as JSON.
    """
    try:
        exporter = MASExporter()
        mas_doc = exporter.export_transformer(
            design_result=request.design_result,
            requirements=request.requirements,
        )
        
        # Generate filename from design info
        core_name = request.design_result.get('core', {}).get('part_number', 'unknown')
        power = request.requirements.get('output_power_W', 0)
        filename = f"transformer_{core_name}_{int(power)}W.mas.json"
        
        return MASExportResponse(
            format="mas",
            version=exporter.MAS_VERSION,
            filename=filename,
            content=mas_doc,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MAS export failed: {str(e)}"
        )


@router.post("/mas/download")
async def download_mas_file(request: TransformerExportRequest):
    """
    Download MAS export as a JSON file.
    
    Returns the MAS document as a downloadable file attachment.
    """
    try:
        exporter = MASExporter()
        mas_json = exporter.export_to_json(
            design_result=request.design_result,
            requirements=request.requirements,
            pretty=request.pretty,
        )
        
        # Generate filename
        core_name = request.design_result.get('core', {}).get('part_number', 'unknown')
        power = request.requirements.get('output_power_W', 0)
        filename = f"transformer_{core_name}_{int(power)}W.mas.json"
        
        return Response(
            content=mas_json,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MAS download failed: {str(e)}"
        )


@router.post("/femm", response_model=FEMMExportResponse)
async def export_to_femm(request: TransformerExportRequest):
    """
    Export transformer design to FEMM Lua script.
    
    FEMM (Finite Element Method Magnetics) is a free 2D FEA tool.
    The generated Lua script creates:
    - Core geometry (E-type cross-section)
    - Material definitions
    - Winding regions with turn counts
    - Circuit definitions for analysis
    
    Open the script in FEMM to simulate the transformer.
    """
    try:
        exporter = FEMMExporter()
        lua_script = exporter.export_lua_script(
            design_result=request.design_result,
            requirements=request.requirements,
        )
        
        # Generate filename
        core_name = request.design_result.get('core', {}).get('part_number', 'unknown')
        power = request.requirements.get('output_power_W', 0)
        filename = f"transformer_{core_name}_{int(power)}W.lua"
        
        return FEMMExportResponse(
            format="femm",
            filename=filename,
            content=lua_script,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"FEMM export failed: {str(e)}"
        )


@router.post("/femm/download")
async def download_femm_file(request: TransformerExportRequest):
    """
    Download FEMM Lua script as a file.
    
    Returns the Lua script as a downloadable file attachment.
    """
    try:
        exporter = FEMMExporter()
        lua_script = exporter.export_lua_script(
            design_result=request.design_result,
            requirements=request.requirements,
        )
        
        # Generate filename
        core_name = request.design_result.get('core', {}).get('part_number', 'unknown')
        power = request.requirements.get('output_power_W', 0)
        filename = f"transformer_{core_name}_{int(power)}W.lua"
        
        return Response(
            content=lua_script,
            media_type="text/x-lua",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"FEMM download failed: {str(e)}"
        )


@router.post("/json/download")
async def download_design_json(request: TransformerExportRequest):
    """
    Download complete design as JSON file.
    
    Exports the raw design result and requirements as a JSON file
    for archival or later import.
    """
    try:
        export_data = {
            "version": "1.0.0",
            "type": "transformer_design",
            "requirements": request.requirements,
            "design_result": request.design_result,
        }
        
        json_content = json.dumps(export_data, indent=2 if request.pretty else None)
        
        # Generate filename
        core_name = request.design_result.get('core', {}).get('part_number', 'unknown')
        power = request.requirements.get('output_power_W', 0)
        filename = f"transformer_design_{core_name}_{int(power)}W.json"
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON export failed: {str(e)}"
        )


@router.get("/formats")
async def get_export_formats():
    """
    Get list of available export formats.
    
    Returns information about each supported export format.
    """
    return {
        "formats": [
            {
                "id": "mas",
                "name": "MAS (Magnetic Agnostic Structure)",
                "extension": ".mas.json",
                "description": "OpenMagnetics JSON format for FEA tools",
                "available": True,
            },
            {
                "id": "femm",
                "name": "FEMM Lua Script",
                "extension": ".lua",
                "description": "Script for FEMM 2D magnetic simulation",
                "available": True,
            },
            {
                "id": "json",
                "name": "Design JSON",
                "extension": ".json",
                "description": "Raw design data for archival/import",
                "available": True,
            },
            {
                "id": "pdf",
                "name": "PDF Report",
                "extension": ".pdf",
                "description": "Printable design report (coming soon)",
                "available": False,
            },
            {
                "id": "step",
                "name": "STEP 3D Model",
                "extension": ".step",
                "description": "3D CAD model (coming soon)",
                "available": False,
            },
        ],
    }