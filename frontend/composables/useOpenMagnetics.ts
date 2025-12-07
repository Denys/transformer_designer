/**
 * Composable for OpenMagnetics API interactions
 * 
 * Provides access to:
 * - Core search (standard and loss-based)
 * - Material property lookup
 * - Core comparison
 * - Database statistics
 */

// ============================================================================
// Types
// ============================================================================

export interface OpenMagneticsCore {
    source: 'openmagnetics'
    name: string
    part_number: string
    manufacturer: string
    geometry: string
    material: string
    Ae_cm2: number
    Wa_cm2: number
    Ap_cm4: number
    Ve_cm3: number
    lm_cm: number
    MLT_cm: number
    At_cm2: number
    weight_g: number
    Bsat_T: number
    mu_i: number
    datasheet_url?: string
}

export interface CoreWithLoss extends OpenMagneticsCore {
    estimated_core_loss_W?: number
    loss_density_kW_m3?: number
    loss_density_mW_cm3?: number
    steinmetz_k?: number
    steinmetz_alpha?: number
    steinmetz_beta?: number
    at_frequency_kHz?: number
    at_Bac_T?: number
    at_temperature_C?: number
}

export interface MaterialProperties {
    name: string
    family: string
    initial_permeability: number
    saturation_flux_T: number
    curie_temp_C: number
    resistivity_ohm_m: number
    density_kg_m3: number
    steinmetz_k: number
    steinmetz_alpha: number
    steinmetz_beta: number
    loss_reference_freq_Hz: number
    loss_reference_B_T: number
    loss_reference_kW_m3: number
    temperature_coefficients: Record<string, number>
}

export interface CoreLossCalculation {
    core_loss_W: number
    loss_density_mW_cm3: number
    loss_density_kW_m3: number
    steinmetz_k: number
    steinmetz_alpha: number
    steinmetz_beta: number
    temperature_C: number
    frequency_Hz: number
    Bac_T: number
    method: string
}

export interface DatabaseSummary {
    available: boolean
    core_count: number
    manufacturers: string[]
    shape_families: string[]
    material_count: number
    error?: string
}

export interface CoreSearchParams {
    min_Ap_cm4?: number
    max_Ap_cm4?: number
    shape_family?: string
    manufacturer?: string
    material?: string
    limit?: number
}

export interface LossBasedSearchParams {
    required_Ap_cm4: number
    frequency_Hz: number
    Bac_T: number
    max_core_loss_W?: number
    max_loss_density_kW_m3?: number
    temperature_C?: number
    preferred_geometry?: string
    preferred_material?: string
    count?: number
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE = 'http://127.0.0.1:8000'

// ============================================================================
// Composable
// ============================================================================

export function useOpenMagnetics() {
    // State
    const loading = ref(false)
    const error = ref<string | null>(null)
    const dbStatus = ref<DatabaseSummary | null>(null)
    const searchResults = ref<CoreWithLoss[]>([])
    const selectedMaterial = ref<MaterialProperties | null>(null)
    const comparisonResults = ref<CoreWithLoss[]>([])
    
    // Cached lists
    const manufacturers = ref<string[]>([])
    const shapesFamilies = ref<string[]>([])
    const materials = ref<string[]>([])
    
    // ========================================================================
    // Database Status & Metadata
    // ========================================================================
    
    async function fetchDatabaseStatus(): Promise<DatabaseSummary | null> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/status`)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const data = await response.json()
            dbStatus.value = data as DatabaseSummary
            
            // Cache lists
            if (dbStatus.value) {
                manufacturers.value = dbStatus.value.manufacturers
                shapesFamilies.value = dbStatus.value.shape_families
            }
            
            return dbStatus.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to fetch database status'
            return null
        } finally {
            loading.value = false
        }
    }
    
    async function fetchManufacturers(): Promise<string[]> {
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/manufacturers`)
            if (response.ok) {
                const data = await response.json()
                manufacturers.value = data.manufacturers || []
            }
        } catch (e) {
            console.error('Failed to fetch manufacturers:', e)
        }
        return manufacturers.value
    }
    
    async function fetchShapeFamilies(): Promise<string[]> {
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/shapes`)
            if (response.ok) {
                const data = await response.json()
                shapesFamilies.value = data.shape_families || []
            }
        } catch (e) {
            console.error('Failed to fetch shape families:', e)
        }
        return shapesFamilies.value
    }
    
    async function fetchMaterials(): Promise<string[]> {
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/materials`)
            if (response.ok) {
                const data = await response.json()
                materials.value = data.materials || []
            }
        } catch (e) {
            console.error('Failed to fetch materials:', e)
        }
        return materials.value
    }
    
    // ========================================================================
    // Core Search
    // ========================================================================
    
    async function searchCores(params: CoreSearchParams): Promise<OpenMagneticsCore[]> {
        loading.value = true
        error.value = null
        searchResults.value = []
        
        try {
            const queryParams = new URLSearchParams()
            
            if (params.min_Ap_cm4 !== undefined) queryParams.append('min_Ap_cm4', params.min_Ap_cm4.toString())
            if (params.max_Ap_cm4 !== undefined) queryParams.append('max_Ap_cm4', params.max_Ap_cm4.toString())
            if (params.shape_family) queryParams.append('shape_family', params.shape_family)
            if (params.manufacturer) queryParams.append('manufacturer', params.manufacturer)
            if (params.material) queryParams.append('material', params.material)
            if (params.limit !== undefined) queryParams.append('limit', params.limit.toString())
            
            const response = await fetch(`${API_BASE}/api/openmagnetics/cores?${queryParams}`)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const data = await response.json()
            searchResults.value = data as CoreWithLoss[]
            
            return searchResults.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Search failed'
            return []
        } finally {
            loading.value = false
        }
    }
    
    async function searchCoresByLoss(params: LossBasedSearchParams): Promise<CoreWithLoss[]> {
        loading.value = true
        error.value = null
        searchResults.value = []
        
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/cores/search-by-loss`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params),
            })
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }
            
            const data = await response.json()
            searchResults.value = data.cores as CoreWithLoss[]
            
            return searchResults.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Loss-based search failed'
            return []
        } finally {
            loading.value = false
        }
    }
    
    async function findSuitableCores(
        required_Ap_cm4: number,
        frequency_Hz: number,
        geometry?: string,
        material?: string,
        count: number = 5,
    ): Promise<CoreWithLoss[]> {
        loading.value = true
        error.value = null
        
        try {
            const queryParams = new URLSearchParams({
                required_Ap_cm4: required_Ap_cm4.toString(),
                frequency_Hz: frequency_Hz.toString(),
                count: count.toString(),
            })
            
            if (geometry) queryParams.append('geometry', geometry)
            if (material) queryParams.append('material', material)
            
            const response = await fetch(`${API_BASE}/api/openmagnetics/cores/suitable?${queryParams}`)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const data = await response.json()
            searchResults.value = data.cores as CoreWithLoss[]
            
            return searchResults.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Search failed'
            return []
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // Material Properties
    // ========================================================================
    
    async function getMaterialProperties(materialName: string): Promise<MaterialProperties | null> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/materials/${encodeURIComponent(materialName)}`)
            
            if (!response.ok) {
                if (response.status === 404) {
                    error.value = `Material '${materialName}' not found`
                    return null
                }
                throw new Error(`HTTP ${response.status}`)
            }
            
            const data = await response.json()
            selectedMaterial.value = data as MaterialProperties
            
            return selectedMaterial.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to get material properties'
            return null
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // Core Loss Calculation
    // ========================================================================
    
    async function calculateCoreLoss(
        coreName: string,
        frequency_Hz: number,
        Bac_T: number,
        temperature_C: number = 100,
        waveform: string = 'sinusoidal',
    ): Promise<CoreLossCalculation | null> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/openmagnetics/cores/calculate-loss`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    core_name: coreName,
                    frequency_Hz,
                    Bac_T,
                    temperature_C,
                    waveform,
                }),
            })
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }
            
            return await response.json() as CoreLossCalculation
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Loss calculation failed'
            return null
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // Core Comparison
    // ========================================================================
    
    async function compareCores(
        coreNames: string[],
        frequency_Hz: number,
        Bac_T: number,
        temperature_C: number = 100,
    ): Promise<CoreWithLoss[]> {
        loading.value = true
        error.value = null
        comparisonResults.value = []
        
        try {
            const queryParams = new URLSearchParams({
                frequency_Hz: frequency_Hz.toString(),
                Bac_T: Bac_T.toString(),
                temperature_C: temperature_C.toString(),
            })
            
            const response = await fetch(`${API_BASE}/api/openmagnetics/cores/compare?${queryParams}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(coreNames),
            })
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }
            
            const data = await response.json()
            comparisonResults.value = data.results as CoreWithLoss[]
            
            return comparisonResults.value
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Comparison failed'
            return []
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // Utility Functions
    // ========================================================================
    
    function clearResults(): void {
        searchResults.value = []
        comparisonResults.value = []
        error.value = null
    }
    
    function clearError(): void {
        error.value = null
    }
    
    // Computed: Check if database is available
    const isAvailable = computed(() => dbStatus.value?.available ?? false)
    const coreCount = computed(() => dbStatus.value?.core_count ?? 0)
    
    return {
        // State
        loading,
        error,
        dbStatus,
        searchResults,
        selectedMaterial,
        comparisonResults,
        
        // Cached lists
        manufacturers,
        shapesFamilies,
        materials,
        
        // Computed
        isAvailable,
        coreCount,
        
        // Methods - Database
        fetchDatabaseStatus,
        fetchManufacturers,
        fetchShapeFamilies,
        fetchMaterials,
        
        // Methods - Search
        searchCores,
        searchCoresByLoss,
        findSuitableCores,
        
        // Methods - Material
        getMaterialProperties,
        
        // Methods - Loss
        calculateCoreLoss,
        compareCores,
        
        // Methods - Utility
        clearResults,
        clearError,
    }
}