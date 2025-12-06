"""
OpenMagnetics Integration via PyMKF

This module provides access to the OpenMagnetics database of over 10,000 cores
from manufacturers like TDK, Ferroxcube, Magnetics, Fair-Rite, etc.

Uses PyMKF (Python wrapper for MKF - Magnetics Knowledge Foundation)
"""

import PyMKF
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class OpenMagneticsDB:
    """
    Interface to the OpenMagnetics database.
    
    Provides access to:
    - 10,000+ cores from major manufacturers
    - 400+ magnetic materials with Steinmetz coefficients
    - Core shapes, bobbins, wires
    - Core loss calculations
    """
    
    def __init__(self):
        """Initialize the OpenMagnetics database connection."""
        # Test database availability by trying to get cores
        try:
            # PyMKF loads databases automatically, just test it works
            cores = PyMKF.get_available_cores()
            self._available = len(cores) > 0
            if self._available:
                logger.info(f"OpenMagnetics database ready: {len(cores)} cores available")
            else:
                logger.warning("OpenMagnetics database returned 0 cores")
        except Exception as e:
            logger.warning(f"Could not access OpenMagnetics database: {e}")
            self._available = False
    
    @property
    def is_available(self) -> bool:
        """Check if OpenMagnetics database is available."""
        return self._available
    
    @lru_cache(maxsize=1)
    def get_core_count(self) -> int:
        """Get total number of cores in database."""
        if not self._available:
            return 0
        try:
            return len(PyMKF.get_available_cores())
        except Exception:
            return 0
    
    @lru_cache(maxsize=1)
    def get_manufacturers(self) -> List[str]:
        """Get list of available core manufacturers."""
        if not self._available:
            return []
        try:
            return PyMKF.get_available_core_manufacturers()
        except Exception:
            return []
    
    @lru_cache(maxsize=1)
    def get_shape_families(self) -> List[str]:
        """Get list of available core shape families (E, ETD, PQ, etc.)."""
        if not self._available:
            return []
        try:
            return PyMKF.get_available_core_shape_families()
        except Exception:
            return []
    
    @lru_cache(maxsize=1)
    def get_material_names(self) -> List[str]:
        """Get list of available material names."""
        if not self._available:
            return []
        try:
            return PyMKF.get_core_material_names()
        except Exception:
            return []
    
    def get_cores(
        self,
        min_Ap_cm4: Optional[float] = None,
        max_Ap_cm4: Optional[float] = None,
        shape_family: Optional[str] = None,
        manufacturer: Optional[str] = None,
        material: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for cores matching specified criteria.
        
        Args:
            min_Ap_cm4: Minimum area product [cm⁴]
            max_Ap_cm4: Maximum area product [cm⁴]
            shape_family: Core shape family (E, ETD, PQ, RM, etc.)
            manufacturer: Manufacturer name (TDK, Ferroxcube, etc.)
            material: Material name (N87, 3C95, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of core dictionaries with standardized format
        """
        if not self._available:
            return []
        
        try:
            all_cores = PyMKF.get_available_cores()
            results = []
            
            for core in all_cores:
                if len(results) >= limit:
                    break
                
                # Extract effective parameters
                processed = core.get('processedDescription', {})
                eff_params = processed.get('effectiveParameters', {})
                
                # Get Ae and calculate approximate Wa and Ap
                Ae_m2 = eff_params.get('effectiveArea', 0)
                Ae_cm2 = Ae_m2 * 1e4  # m² to cm²
                
                # Get window area from windingWindows
                winding_windows = processed.get('windingWindows', [])
                Wa_m2 = sum(w.get('area', 0) for w in winding_windows)
                Wa_cm2 = Wa_m2 * 1e4  # m² to cm²
                
                # Calculate Ap
                Ap_cm4 = Ae_cm2 * Wa_cm2
                
                # Filter by Ap range
                if min_Ap_cm4 is not None and Ap_cm4 < min_Ap_cm4:
                    continue
                if max_Ap_cm4 is not None and Ap_cm4 > max_Ap_cm4:
                    continue
                
                # Get core info
                name = core.get('name', '')
                mfr_info = core.get('manufacturerInfo', {})
                mfr_name = mfr_info.get('name', '') if mfr_info else ''
                
                # Filter by manufacturer
                if manufacturer and manufacturer.lower() not in mfr_name.lower():
                    continue
                
                # Get material info  
                func_desc = core.get('functionalDescription', {})
                mat_info = func_desc.get('material', {})
                mat_name = mat_info.get('family', '') if mat_info else ''
                
                # Filter by material
                if material and material.lower() not in mat_name.lower():
                    continue
                
                # Get shape family from name
                core_shape = name.split()[0] if name else ''
                
                # Filter by shape family
                if shape_family and not core_shape.upper().startswith(shape_family.upper()):
                    continue
                
                # Get other parameters
                Ve_m3 = eff_params.get('effectiveVolume', 0)
                Ve_cm3 = Ve_m3 * 1e6  # m³ to cm³
                
                lm_m = eff_params.get('effectiveLength', 0)
                lm_cm = lm_m * 100  # m to cm
                
                # Get saturation flux density from material
                Bsat = 0.4  # Default for ferrite
                if mat_info:
                    sat_data = mat_info.get('saturation', [])
                    if sat_data:
                        Bsat = sat_data[0].get('magneticFluxDensity', 0.4)
                
                # Build standardized core entry
                core_entry = {
                    'source': 'openmagnetics',
                    'name': name,
                    'part_number': mfr_info.get('reference', name) if mfr_info else name,
                    'manufacturer': mfr_name,
                    'geometry': core_shape,
                    'material': mat_name,
                    'Ae_cm2': round(Ae_cm2, 4),
                    'Wa_cm2': round(Wa_cm2, 4),
                    'Ap_cm4': round(Ap_cm4, 4),
                    'Ve_cm3': round(Ve_cm3, 4),
                    'lm_cm': round(lm_cm, 2),
                    'Bsat_T': Bsat,
                    'datasheet_url': mfr_info.get('datasheetUrl', '') if mfr_info else '',
                }
                
                results.append(core_entry)
            
            # Sort by Ap (smallest first for transformer selection)
            results.sort(key=lambda c: c['Ap_cm4'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching OpenMagnetics cores: {e}")
            return []
    
    def find_suitable_cores(
        self,
        required_Ap_cm4: float,
        frequency_Hz: float,
        preferred_geometry: Optional[str] = None,
        preferred_material: Optional[str] = None,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find cores suitable for a given Ap requirement.
        
        Args:
            required_Ap_cm4: Required area product [cm⁴]
            frequency_Hz: Operating frequency [Hz]
            preferred_geometry: Preferred shape (EE, ETD, PQ, etc.)
            preferred_material: Preferred material (N87, 3C95, etc.)
            count: Number of results to return
            
        Returns:
            List of suitable cores, smallest Ap first
        """
        # Search for cores with Ap >= 90% of required
        min_Ap = required_Ap_cm4 * 0.9
        max_Ap = required_Ap_cm4 * 5.0  # Don't go too oversized
        
        cores = self.get_cores(
            min_Ap_cm4=min_Ap,
            max_Ap_cm4=max_Ap,
            shape_family=preferred_geometry,
            material=preferred_material,
            limit=count * 10,  # Get more to filter
        )
        
        # Filter by frequency suitability
        if frequency_Hz > 1000:
            # High frequency - prefer ferrite materials
            # Ferrite families include: 3C, 3F, N (TDK), PC (TDK), etc.
            ferrite_families = ['3C', '3F', '3E', 'N', 'PC', 'P', 'R', 'T']
            filtered = []
            for c in cores:
                mat = c.get('material', '').upper()
                is_ferrite = any(mat.startswith(fam.upper()) for fam in ferrite_families)
                if is_ferrite or not mat:  # Include if ferrite or unknown
                    filtered.append(c)
            cores = filtered if filtered else cores  # Fall back to all if none match
        
        return cores[:count]
    
    def get_core_loss(
        self,
        core_name: str,
        frequency_Hz: float,
        Bac_T: float,
        temperature_C: float = 100,
    ) -> Optional[Dict[str, float]]:
        """
        Calculate core loss using OpenMagnetics models.
        
        Args:
            core_name: Core name from database
            frequency_Hz: Operating frequency [Hz]
            Bac_T: AC flux density [T]
            temperature_C: Operating temperature [°C]
            
        Returns:
            Dict with core_loss_W, loss_density_W_m3 or None if calculation fails
        """
        if not self._available:
            return None
        
        try:
            # Find the core
            cores = PyMKF.get_available_cores()
            matching = [c for c in cores if c.get('name', '') == core_name]
            
            if not matching:
                return None
            
            core = matching[0]
            
            # Get material info for Steinmetz calculation
            func_desc = core.get('functionalDescription', {})
            mat_info = func_desc.get('material', {})
            mat_name = mat_info.get('family', 'ferrite')
            
            # Try to get Steinmetz coefficients
            try:
                steinmetz = PyMKF.get_core_material_steinmetz_coefficients(mat_name)
                k = steinmetz.get('k', 1e-6)
                alpha = steinmetz.get('alpha', 1.3)
                beta = steinmetz.get('beta', 2.5)
            except Exception:
                # Use defaults
                k, alpha, beta = 1e-6, 1.3, 2.5
            
            # Get volume
            processed = core.get('processedDescription', {})
            eff_params = processed.get('effectiveParameters', {})
            Ve_m3 = eff_params.get('effectiveVolume', 0)
            
            # Calculate loss: P = k * f^alpha * B^beta * Ve
            f_kHz = frequency_Hz / 1000
            loss_density = k * (f_kHz ** alpha) * (Bac_T ** beta)  # W/m³
            core_loss = loss_density * Ve_m3 * 1000  # W
            
            return {
                'core_loss_W': core_loss,
                'loss_density_W_m3': loss_density,
                'steinmetz_k': k,
                'steinmetz_alpha': alpha,
                'steinmetz_beta': beta,
            }
            
        except Exception as e:
            logger.error(f"Error calculating core loss: {e}")
            return None
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the database."""
        if not self._available:
            return {
                'available': False,
                'error': 'OpenMagnetics database not available',
            }
        
        try:
            return {
                'available': True,
                'core_count': self.get_core_count(),
                'manufacturers': self.get_manufacturers(),
                'shape_families': self.get_shape_families(),
                'material_count': len(self.get_material_names()),
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
            }


# Singleton instance
_db_instance: Optional[OpenMagneticsDB] = None


def get_openmagnetics_db() -> OpenMagneticsDB:
    """Get the OpenMagnetics database singleton instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = OpenMagneticsDB()
    return _db_instance
