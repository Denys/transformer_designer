"""
Silicon-Steel Core Database Loader

Provides access to laminated silicon-steel E/I cores for LF transformer applications.
This complements the OpenMagnetics database which only has ferrite/powder cores.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


# Path to the silicon-steel core database
DATA_FILE = Path(__file__).parent.parent / "data" / "silicon_steel_cores.json"


class SiliconSteelCoreDB:
    """Database of silicon-steel laminated cores for LF applications."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._cores: List[Dict[str, Any]] = []
        self._materials: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def load(self) -> bool:
        """Load the core database from JSON file."""
        if self._loaded:
            return True
            
        try:
            if not DATA_FILE.exists():
                logger.warning(f"Silicon-steel core database not found: {DATA_FILE}")
                return False
                
            with open(DATA_FILE, 'r') as f:
                self._data = json.load(f)
            
            self._cores = self._data.get("cores", [])
            self._materials = self._data.get("material_grades", {})
            self._loaded = True
            
            logger.info(f"Loaded {len(self._cores)} silicon-steel cores")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load silicon-steel database: {e}")
            return False
    
    def find_suitable_cores(
        self,
        required_Ae_cm2: float,
        required_Wa_cm2: Optional[float] = None,
        min_Bmax_T: float = 1.0,
        geometry: Optional[str] = None,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find silicon-steel cores matching requirements.
        
        Args:
            required_Ae_cm2: Minimum effective core area [cm²]
            required_Wa_cm2: Minimum window area [cm²] (optional)
            min_Bmax_T: Minimum Bmax rating [T]
            geometry: Core geometry filter (e.g., "EI")
            count: Maximum number of cores to return
            
        Returns:
            List of matching cores, sorted by Ae (smallest suitable first)
        """
        if not self._loaded:
            self.load()
        
        suitable = []
        
        for core in self._cores:
            # Check Ae
            if core.get("Ae_cm2", 0) < required_Ae_cm2 * 0.9:
                continue
            
            # Check Wa if specified
            if required_Wa_cm2 and core.get("Wa_cm2", 0) < required_Wa_cm2 * 0.9:
                continue
            
            # Check Bmax
            if core.get("Bmax_T", 0) < min_Bmax_T:
                continue
            
            # Check geometry
            if geometry and core.get("geometry", "").lower() != geometry.lower():
                continue
            
            suitable.append(core)
        
        # Sort by Ae (smallest first that meets requirements)
        suitable.sort(key=lambda x: x.get("Ae_cm2", 0))
        
        return suitable[:count]
    
    def get_core_by_part_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific core by part number."""
        if not self._loaded:
            self.load()
            
        for core in self._cores:
            if core.get("part_number", "").lower() == part_number.lower():
                return core
        return None
    
    def get_material_properties(self, grade: str) -> Optional[Dict[str, Any]]:
        """Get material properties for a grade (M3, M4, M5, M6)."""
        if not self._loaded:
            self.load()
        return self._materials.get(grade)
    
    def list_all_cores(self) -> List[Dict[str, Any]]:
        """Return all cores in the database."""
        if not self._loaded:
            self.load()
        return self._cores.copy()
    
    def calculate_core_loss(
        self,
        core: Dict[str, Any],
        Bmax_T: float,
        frequency_Hz: float,
        duty_cycle: float = 1.0,
    ) -> float:
        """
        Estimate core loss for a core at given operating conditions.
        
        Uses simplified Steinmetz approximation for silicon steel:
        P = k * f^α * B^β * volume
        
        Args:
            core: Core specification dict
            Bmax_T: Operating flux density [T]
            frequency_Hz: Operating frequency [Hz]
            duty_cycle: Duty cycle (0-1) for pulse applications
            
        Returns:
            Estimated core loss [W]
        """
        grade = core.get("material_grade", "M5")
        material = self._materials.get(grade, {})
        
        # Reference loss at 1.5T, 50Hz
        P_ref = material.get("core_loss_W_kg_1_5T_50Hz", 1.15)  # W/kg
        
        # Steinmetz scaling (simplified)
        # α ≈ 1.6 for frequency, β ≈ 2.0 for flux density
        alpha = 1.6
        beta = 2.0
        
        # Scale loss
        P_scaled = P_ref * (frequency_Hz / 50) ** alpha * (Bmax_T / 1.5) ** beta
        
        # Apply duty cycle (for pulsed applications)
        P_scaled *= duty_cycle
        
        # Calculate total loss
        weight_kg = core.get("weight_g", 1000) / 1000
        total_loss_W = P_scaled * weight_kg
        
        return total_loss_W


# Singleton instance
_db_instance: Optional[SiliconSteelCoreDB] = None


def get_silicon_steel_db() -> SiliconSteelCoreDB:
    """Get the singleton silicon-steel core database."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SiliconSteelCoreDB()
        _db_instance.load()
    return _db_instance
