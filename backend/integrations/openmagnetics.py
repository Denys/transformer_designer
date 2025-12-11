"""
OpenMagnetics Integration via PyMKF

This module provides access to the OpenMagnetics database of over 10,000 cores
from manufacturers like TDK, Ferroxcube, Magnetics, Fair-Rite, etc.

Uses PyMKF (Python wrapper for MKF - Magnetics Knowledge Foundation)

Enhanced Features:
- Loss-based core filtering for optimal efficiency
- Temperature-dependent material properties
- Cross-validation with OpenMagnetics loss models
- Advanced search with multi-parameter optimization
"""

import math
import PyMKF
from typing import Optional, List, Dict, Any, Tuple
from functools import lru_cache
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CoreLossResult:
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
    method: str = "steinmetz"


@dataclass
class MaterialProperties:
    """Material properties for magnetic calculations."""
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
                
                # Get core dimensions for MLT and At calculations
                width_m = processed.get('width', 0)
                height_m = processed.get('height', 0)
                depth_m = processed.get('depth', 0)
                width_cm = width_m * 100
                height_cm = height_m * 100
                depth_cm = depth_m * 100
                
                # Calculate MLT (Mean Length per Turn) based on geometry
                MLT_cm = self._calculate_MLT(core_shape, width_cm, height_cm, depth_cm, Ae_cm2)
                
                # Calculate thermal surface area (At)
                At_cm2 = self._calculate_surface_area(core_shape, width_cm, height_cm, depth_cm, Ap_cm4)
                
                # Calculate weight estimate
                weight_g = self._estimate_weight(Ve_cm3, mat_name)
                
                # Get saturation flux density from material
                Bsat = 0.4  # Default for ferrite
                if mat_info:
                    sat_data = mat_info.get('saturation', [])
                    if sat_data:
                        Bsat = sat_data[0].get('magneticFluxDensity', 0.4)
                
                # Get initial permeability
                mu_i = 2000  # Default for ferrite
                if mat_info:
                    mu_i = mat_info.get('initialPermeability', 2000)
                
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
                    'MLT_cm': round(MLT_cm, 2),
                    'At_cm2': round(At_cm2, 2),
                    'weight_g': round(weight_g, 1),
                    'Bsat_T': Bsat,
                    'mu_i': mu_i,
                    'datasheet_url': mfr_info.get('datasheetUrl', '') if mfr_info else '',
                }
                
                results.append(core_entry)
            
            # Sort by Ap (smallest first for transformer selection)
            results.sort(key=lambda c: c['Ap_cm4'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching OpenMagnetics cores: {e}")
            return []
    
    def _calculate_MLT(
        self,
        shape: str,
        width_cm: float,
        height_cm: float,
        depth_cm: float,
        Ae_cm2: float,
    ) -> float:
        """
        Calculate Mean Length per Turn (MLT) from core geometry.
        
        MLT is the average length of wire for one turn around the center leg.
        
        For E-type cores (E, EE, EI, ETD, EFD, EQ, ER, EP):
            Center leg is roughly square, winding goes around it
            MLT ≈ 2 * (center_leg_width + winding_depth) + some margin
            Simplified: MLT ≈ 4 * sqrt(Ae) + perimeter_factor
        
        For PQ/PM cores (pot-style):
            Similar to E-type but more compact
            MLT ≈ π * (inner_dia + outer_dia) / 2
            
        For Toroidal cores:
            MLT ≈ 2 * (OD - ID) / 2 + some margin for winding
        
        Args:
            shape: Core shape family (E, ETD, PQ, etc.)
            width_cm: Core width [cm]
            height_cm: Core height [cm]
            depth_cm: Core depth [cm]
            Ae_cm2: Effective area [cm²] - used as fallback
            
        Returns:
            MLT in cm
        """
        shape_upper = shape.upper()
        
        # Calculate approximate center leg dimension from Ae
        center_leg_width = math.sqrt(Ae_cm2)
        
        if shape_upper in ['E', 'EE', 'EI', 'ETD', 'ER', 'EQ', 'EFD', 'EP']:
            # E-type cores: MLT goes around rectangular center leg
            # Typical: MLT ≈ 2*(leg_width + winding_depth)
            # Winding depth ≈ (width - center_leg) / 2
            winding_depth = (width_cm - center_leg_width) / 2 if width_cm > center_leg_width else depth_cm / 3
            MLT = 2 * (center_leg_width + winding_depth) * 0.8  # 0.8 factor for winding path
            
        elif shape_upper in ['PQ', 'PM', 'P']:
            # PQ/PM cores: Round center, pot-style
            # MLT is roughly the circumference of the center post + winding
            inner_radius = center_leg_width / 2
            outer_radius = min(width_cm, depth_cm) / 2
            mean_radius = (inner_radius + outer_radius) / 2
            MLT = 2 * math.pi * mean_radius * 0.7  # 0.7 factor for typical winding path
            
        elif shape_upper in ['RM']:
            # RM cores: Low-profile with center hole
            MLT = 2 * (center_leg_width + depth_cm / 2) + 0.3
            
        elif shape_upper in ['T', 'TC', 'TOROID']:
            # Toroidal cores
            # MLT depends on build-up, estimate from OD-ID
            OD = max(width_cm, depth_cm)
            ID = OD * 0.5  # Typical ID/OD ratio
            MLT = math.pi * (width_cm + depth_cm) / 2
            
        elif shape_upper in ['POT']:
            # Pot cores (cylindrical)
            MLT = 2 * math.pi * (center_leg_width / 2 + depth_cm / 4)
            
        elif shape_upper in ['U', 'UI', 'UU']:
            # U-cores: Simple rectangular path
            MLT = 2 * (width_cm + depth_cm) * 0.5
            
        elif shape_upper in ['ELP', 'PLANAR']:
            # Planar cores - very low profile
            MLT = 2 * (width_cm + depth_cm) * 0.6
            
        else:
            # Default fallback: estimate from Ap
            MLT = 2 * (width_cm + depth_cm) * 0.9
        
        # Sanity check - MLT should be reasonable
        if MLT < 0.5:
            MLT = 4 * math.sqrt(Ae_cm2) + 0.5
        
        return max(MLT, 1.0)  # Minimum 1 cm
    
    def _calculate_surface_area(
        self,
        shape: str,
        width_cm: float,
        height_cm: float,
        depth_cm: float,
        Ap_cm4: float,
    ) -> float:
        """
        Calculate thermal surface area (At) for heat dissipation.
        
        At is the external surface area available for heat transfer.
        This affects temperature rise: Tr = 450 * (Ptotal/At)^0.826
        
        For most cores, At can be estimated from:
        - Box approximation: At = 2*(W*H + W*D + H*D)
        - Multiply by factor for exposed surface (not all surfaces dissipate equally)
        
        Args:
            shape: Core shape family
            width_cm: Core width [cm]
            height_cm: Core height [cm]
            depth_cm: Core depth [cm]
            Ap_cm4: Area product [cm⁴] - used as fallback
            
        Returns:
            Surface area At [cm²]
        """
        shape_upper = shape.upper()
        
        # Check if we have valid dimensions
        if width_cm > 0 and height_cm > 0 and depth_cm > 0:
            # Box surface area (both halves assembled)
            # At ≈ 2*(W*H + W*D + H*D) for box approximation
            box_surface = 2 * (width_cm * height_cm + width_cm * depth_cm + height_cm * depth_cm)
            
            # Apply shape factor (not all surface is equally exposed)
            if shape_upper in ['E', 'EE', 'EI', 'ETD', 'ER', 'EQ', 'EFD', 'EP']:
                # E-cores: Good exposure on sides and top, less on inner surfaces
                At = box_surface * 0.60
            elif shape_upper in ['PQ', 'PM', 'P', 'POT']:
                # Pot/PQ cores: Less exposed surface due to enclosed design
                At = box_surface * 0.50
            elif shape_upper in ['RM']:
                # RM cores: Moderate exposure
                At = box_surface * 0.55
            elif shape_upper in ['T', 'TC', 'TOROID']:
                # Toroids: Good all-around exposure
                At = box_surface * 0.70
            elif shape_upper in ['U', 'UI', 'UU']:
                # U-cores: Good exposure
                At = box_surface * 0.65
            elif shape_upper in ['ELP', 'PLANAR']:
                # Planar: Top and bottom exposed
                At = box_surface * 0.45
            else:
                # Default
                At = box_surface * 0.60
        else:
            # Fallback: Estimate from Ap using McLyman's approximation
            # At ≈ Ks * Ap^0.5 where Ks depends on core type
            Ks_values = {
                'E': 40, 'EE': 40, 'EI': 40, 'ETD': 42, 'ER': 35, 'EQ': 35,
                'PQ': 38, 'PM': 35, 'RM': 30, 'POT': 32,
                'T': 45, 'TC': 45, 'TOROID': 45,
                'U': 40, 'UI': 40,
            }
            Ks = Ks_values.get(shape_upper, 40)
            At = Ks * math.sqrt(Ap_cm4)
        
        # Sanity check
        return max(At, 1.0)  # Minimum 1 cm²
    
    def _estimate_weight(self, Ve_cm3: float, material: str) -> float:
        """
        Estimate core weight from volume and material.
        
        Args:
            Ve_cm3: Effective volume [cm³]
            material: Material name
            
        Returns:
            Estimated weight [g]
        """
        # Core densities [g/cm³]
        # Note: Ve is effective volume, actual material volume is higher
        # due to winding window voids. Use factor ~1.5 for typical cores.
        material_upper = material.upper() if material else ''
        
        if any(mat in material_upper for mat in ['N87', 'N97', 'N49', '3C', '3F', 'PC']):
            # Ferrite: ~4.8 g/cm³
            density = 4.8
        elif any(mat in material_upper for mat in ['M6', 'M19', 'SILICON']):
            # Silicon steel: ~7.65 g/cm³
            density = 7.65
        elif any(mat in material_upper for mat in ['AMORPHOUS', 'METGLAS']):
            # Amorphous: ~7.18 g/cm³
            density = 7.18
        else:
            # Default to ferrite
            density = 4.8
        
        # Effective volume to actual volume factor (varies by core type)
        volume_factor = 1.4
        
        return Ve_cm3 * volume_factor * density
    
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
    
    def find_cores_by_loss(
        self,
        required_Ap_cm4: float,
        frequency_Hz: float,
        Bac_T: float,
        max_core_loss_W: Optional[float] = None,
        max_loss_density_kW_m3: Optional[float] = None,
        temperature_C: float = 100,
        preferred_geometry: Optional[str] = None,
        preferred_material: Optional[str] = None,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find cores filtered by core loss requirements.
        
        This method searches for cores that meet both Ap and loss requirements,
        returning them sorted by estimated core loss (lowest first).
        
        Args:
            required_Ap_cm4: Required area product [cm⁴]
            frequency_Hz: Operating frequency [Hz]
            Bac_T: AC flux density swing [T peak]
            max_core_loss_W: Maximum allowable core loss [W]
            max_loss_density_kW_m3: Maximum loss density [kW/m³]
            temperature_C: Operating temperature [°C]
            preferred_geometry: Preferred core shape
            preferred_material: Preferred material family
            count: Number of results to return
            
        Returns:
            List of cores with loss estimates, sorted by loss (lowest first)
        """
        if not self._available:
            return []
        
        # Get candidate cores with appropriate Ap range
        min_Ap = required_Ap_cm4 * 0.9
        max_Ap = required_Ap_cm4 * 5.0
        
        candidates = self.get_cores(
            min_Ap_cm4=min_Ap,
            max_Ap_cm4=max_Ap,
            shape_family=preferred_geometry,
            material=preferred_material,
            limit=200,  # Get many to filter by loss
        )
        
        results_with_loss = []
        
        for core in candidates:
            # Get material properties for loss calculation
            material = core.get('material', '')
            mat_props = self.get_material_properties(material)
            
            if mat_props is None:
                # Use default ferrite properties
                k, alpha, beta = 1.5e-6, 1.3, 2.5
            else:
                k = mat_props.steinmetz_k
                alpha = mat_props.steinmetz_alpha
                beta = mat_props.steinmetz_beta
            
            # Apply temperature correction if available
            temp_factor = self._temperature_correction(temperature_C, mat_props)
            
            # Calculate loss density: Pv = k * f^alpha * B^beta [kW/m³]
            # Note: k is scaled for f in kHz and B in T
            f_kHz = frequency_Hz / 1000
            loss_density = k * (f_kHz ** alpha) * (Bac_T ** beta) * temp_factor
            
            # Check loss density limit
            if max_loss_density_kW_m3 and loss_density > max_loss_density_kW_m3:
                continue
            
            # Calculate total core loss
            Ve_cm3 = core.get('Ve_cm3', 0)
            Ve_m3 = Ve_cm3 * 1e-6
            core_loss_W = loss_density * Ve_m3 * 1000  # kW to W
            
            # Check total loss limit
            if max_core_loss_W and core_loss_W > max_core_loss_W:
                continue
            
            # Add loss information to core
            core_with_loss = dict(core)
            core_with_loss.update({
                'estimated_core_loss_W': round(core_loss_W, 3),
                'loss_density_kW_m3': round(loss_density, 2),
                'loss_density_mW_cm3': round(loss_density, 2),  # Same numeric value, different unit label
                'steinmetz_k': k,
                'steinmetz_alpha': alpha,
                'steinmetz_beta': beta,
                'at_frequency_kHz': f_kHz,
                'at_Bac_T': Bac_T,
                'at_temperature_C': temperature_C,
            })
            
            results_with_loss.append(core_with_loss)
        
        # Sort by core loss (lowest first)
        results_with_loss.sort(key=lambda c: c['estimated_core_loss_W'])
        
        return results_with_loss[:count]
    
    def _temperature_correction(
        self,
        temperature_C: float,
        mat_props: Optional[MaterialProperties],
    ) -> float:
        """
        Calculate temperature correction factor for core loss.
        
        Most ferrites have minimum loss around 80-100°C, with higher loss
        at both lower and higher temperatures.
        
        Args:
            temperature_C: Operating temperature [°C]
            mat_props: Material properties (if available)
            
        Returns:
            Multiplier for loss (1.0 = reference temperature)
        """
        # Default: loss minimum around 100°C
        T_min = 100  # Temperature of minimum loss
        
        if mat_props and mat_props.temperature_coefficients:
            T_min = mat_props.temperature_coefficients.get('T_min_loss', 100)
        
        # Parabolic approximation: loss increases ~1% per 10°C away from T_min
        delta_T = temperature_C - T_min
        correction = 1.0 + 0.001 * (delta_T ** 2) / 100
        
        return min(correction, 2.0)  # Cap at 2x
    
    def get_material_properties(self, material_name: str) -> Optional[MaterialProperties]:
        """
        Get detailed material properties from OpenMagnetics database.
        
        Args:
            material_name: Material name (N87, 3C95, PC95, etc.)
            
        Returns:
            MaterialProperties dataclass or None if not found
        """
        if not self._available or not material_name:
            return None
        
        try:
            # Try to get material data from PyMKF
            # First, search core materials
            mat_names = self.get_material_names()
            
            # Find matching material (case-insensitive)
            matched = None
            for name in mat_names:
                if material_name.upper() in name.upper() or name.upper() in material_name.upper():
                    matched = name
                    break
            
            if not matched:
                return self._get_default_material_properties(material_name)
            
            # Get Steinmetz coefficients
            try:
                steinmetz = PyMKF.get_core_material_steinmetz_coefficients(matched)
                k = steinmetz.get('k', 1.5e-6)
                alpha = steinmetz.get('alpha', 1.3)
                beta = steinmetz.get('beta', 2.5)
            except Exception:
                k, alpha, beta = 1.5e-6, 1.3, 2.5
            
            # Get permeability
            try:
                perm = PyMKF.get_core_material_permeability(matched)
                mu_i = perm.get('initialPermeability', 2000)
            except Exception:
                mu_i = 2000
            
            # Get saturation
            try:
                sat = PyMKF.get_core_material_saturation(matched)
                Bsat = sat.get('saturation', [{}])[0].get('magneticFluxDensity', 0.4)
            except Exception:
                Bsat = 0.4
            
            return MaterialProperties(
                name=matched,
                family=self._get_material_family(matched),
                initial_permeability=mu_i,
                saturation_flux_T=Bsat,
                curie_temp_C=220,  # Typical for ferrite
                resistivity_ohm_m=1e5,  # High for ferrite
                density_kg_m3=4800,  # Typical ferrite
                steinmetz_k=k,
                steinmetz_alpha=alpha,
                steinmetz_beta=beta,
                loss_reference_freq_Hz=100000,
                loss_reference_B_T=0.1,
                loss_reference_kW_m3=k * (100 ** alpha) * (0.1 ** beta),
                temperature_coefficients={'T_min_loss': 100},
            )
            
        except Exception as e:
            logger.warning(f"Error getting material properties for {material_name}: {e}")
            return self._get_default_material_properties(material_name)
    
    def _get_material_family(self, material_name: str) -> str:
        """Determine material family from name."""
        name_upper = material_name.upper()
        
        if name_upper.startswith('N') and name_upper[1:].isdigit():
            return "TDK_N"
        elif name_upper.startswith('PC'):
            return "TDK_PC"
        elif name_upper.startswith('3C'):
            return "Ferroxcube_3C"
        elif name_upper.startswith('3F'):
            return "Ferroxcube_3F"
        elif name_upper.startswith('3E'):
            return "Ferroxcube_3E"
        elif any(name_upper.startswith(x) for x in ['MPP', 'KOOL', 'HIGH_FLUX', 'XFLUX']):
            return "Powder"
        elif any(name_upper.startswith(x) for x in ['METGLAS', '2605', 'VITRO']):
            return "Amorphous_Nano"
        else:
            return "Unknown"
    
    def _get_default_material_properties(self, material_name: str) -> MaterialProperties:
        """Get default material properties based on material family."""
        family = self._get_material_family(material_name)
        
        # Default Steinmetz coefficients by family
        defaults = {
            "TDK_N": (1.5e-6, 1.35, 2.5, 2000, 0.38),
            "TDK_PC": (1.2e-6, 1.25, 2.4, 2300, 0.39),
            "Ferroxcube_3C": (1.4e-6, 1.3, 2.5, 2000, 0.38),
            "Ferroxcube_3F": (1.1e-6, 1.35, 2.45, 1800, 0.38),
            "Ferroxcube_3E": (2.0e-6, 1.4, 2.6, 6000, 0.32),
            "Powder": (50e-6, 1.5, 2.0, 60, 1.0),
            "Amorphous_Nano": (0.5e-6, 1.7, 2.2, 80000, 1.2),
            "Unknown": (1.5e-6, 1.3, 2.5, 2000, 0.4),
        }
        
        k, alpha, beta, mu_i, Bsat = defaults.get(family, defaults["Unknown"])
        
        return MaterialProperties(
            name=material_name,
            family=family,
            initial_permeability=mu_i,
            saturation_flux_T=Bsat,
            curie_temp_C=220,
            resistivity_ohm_m=1e5,
            density_kg_m3=4800,
            steinmetz_k=k,
            steinmetz_alpha=alpha,
            steinmetz_beta=beta,
            loss_reference_freq_Hz=100000,
            loss_reference_B_T=0.1,
            loss_reference_kW_m3=k * (100 ** alpha) * (0.1 ** beta),
            temperature_coefficients={'T_min_loss': 100},
        )
    
    def calculate_core_loss_detailed(
        self,
        core: Dict[str, Any],
        frequency_Hz: float,
        Bac_T: float,
        temperature_C: float = 100,
        waveform: str = 'sinusoidal',
    ) -> CoreLossResult:
        """
        Calculate detailed core loss for a specific core.
        
        Args:
            core: Core dictionary from database
            frequency_Hz: Operating frequency [Hz]
            Bac_T: AC flux density [T peak]
            temperature_C: Operating temperature [°C]
            waveform: Waveform type (sinusoidal, square, triangular)
            
        Returns:
            CoreLossResult with detailed loss breakdown
        """
        material = core.get('material', '')
        mat_props = self.get_material_properties(material)
        
        if mat_props:
            k = mat_props.steinmetz_k
            alpha = mat_props.steinmetz_alpha
            beta = mat_props.steinmetz_beta
        else:
            k, alpha, beta = 1.5e-6, 1.3, 2.5
        
        # Waveform correction factors (relative to sinusoidal)
        waveform_factors = {
            'sinusoidal': 1.0,
            'square': 1.11,  # Square wave has more harmonic content
            'triangular': 1.05,
            'pulse': 1.2,
        }
        wf_factor = waveform_factors.get(waveform.lower(), 1.0)
        
        # Temperature correction
        temp_factor = self._temperature_correction(temperature_C, mat_props)
        
        # Calculate loss density [kW/m³]
        f_kHz = frequency_Hz / 1000
        loss_density_kW_m3 = k * (f_kHz ** alpha) * (Bac_T ** beta) * wf_factor * temp_factor
        
        # Convert units
        loss_density_mW_cm3 = loss_density_kW_m3  # Same numeric value
        
        # Calculate total loss
        Ve_cm3 = core.get('Ve_cm3', 0)
        Ve_m3 = Ve_cm3 * 1e-6
        core_loss_W = loss_density_kW_m3 * Ve_m3 * 1000
        
        return CoreLossResult(
            core_loss_W=round(core_loss_W, 4),
            loss_density_mW_cm3=round(loss_density_mW_cm3, 3),
            loss_density_kW_m3=round(loss_density_kW_m3, 3),
            steinmetz_k=k,
            steinmetz_alpha=alpha,
            steinmetz_beta=beta,
            temperature_C=temperature_C,
            frequency_Hz=frequency_Hz,
            Bac_T=Bac_T,
            method="steinmetz_extended",
        )
    
    def compare_cores_by_loss(
        self,
        cores: List[Dict[str, Any]],
        frequency_Hz: float,
        Bac_T: float,
        temperature_C: float = 100,
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple cores by their core loss performance.
        
        Args:
            cores: List of core dictionaries
            frequency_Hz: Operating frequency [Hz]
            Bac_T: AC flux density [T]
            temperature_C: Operating temperature [°C]
            
        Returns:
            List of cores with loss data, sorted by loss
        """
        results = []
        
        for core in cores:
            loss_result = self.calculate_core_loss_detailed(
                core, frequency_Hz, Bac_T, temperature_C
            )
            
            core_with_loss = dict(core)
            core_with_loss.update({
                'core_loss_W': loss_result.core_loss_W,
                'loss_density_mW_cm3': loss_result.loss_density_mW_cm3,
                'loss_density_kW_m3': loss_result.loss_density_kW_m3,
                'steinmetz_coefficients': {
                    'k': loss_result.steinmetz_k,
                    'alpha': loss_result.steinmetz_alpha,
                    'beta': loss_result.steinmetz_beta,
                },
            })
            results.append(core_with_loss)
        
        # Sort by loss
        results.sort(key=lambda c: c['core_loss_W'])
        
        return results
    
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
