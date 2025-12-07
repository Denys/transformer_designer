/**
 * Composable for transformer design API interactions
 *
 * Provides type-safe interfaces matching the FastAPI Pydantic models
 */

// ============================================================================
// Enums and Type Unions
// ============================================================================

export type TransformerType = 'power_lf' | 'power_hf' | 'flyback' | 'forward' | 'pulse'
export type WaveformType = 'sinusoidal' | 'square' | 'triangular' | 'pulse'
export type DesignMethodType = 'auto' | 'ap_mclyman' | 'kg_mclyman' | 'kgfe_erickson'
export type CoolingType = 'natural' | 'forced'
export type StatusType = 'pass' | 'warning' | 'fail'
export type ConfidenceLevel = 'high' | 'medium' | 'low'
export type WireType = 'solid' | 'litz'
export type CoreSource = 'local' | 'openmagnetics'

// ============================================================================
// Request Types
// ============================================================================

export interface TransformerRequirements {
    // Power specifications
    output_power_W: number
    efficiency_percent: number
    regulation_percent: number
    
    // Voltage specifications
    primary_voltage_V: number
    secondary_voltage_V: number
    
    // Frequency and waveform
    frequency_Hz: number
    waveform: WaveformType
    duty_cycle?: number
    
    // Operating conditions
    ambient_temp_C: number
    max_temp_rise_C: number
    cooling: CoolingType
    
    // Design preferences
    transformer_type?: TransformerType
    preferred_core_geometry?: string | null
    preferred_material?: string | null
    design_method: DesignMethodType
    
    // Design parameters
    max_current_density_A_cm2: number
    window_utilization_Ku: number
}

// ============================================================================
// Response Types - Core Selection
// ============================================================================

export interface CoreSelection {
    manufacturer: string
    part_number: string
    geometry: string
    material: string
    source: CoreSource
    datasheet_url?: string | null
    
    // Core dimensions
    Ae_cm2: number
    Wa_cm2: number
    Ap_cm4: number
    MLT_cm: number
    lm_cm: number
    Ve_cm3: number
    At_cm2: number
    weight_g: number
    
    // Material properties
    Bsat_T: number
    Bmax_T: number
    mu_i: number
}

// ============================================================================
// Response Types - Winding Design
// ============================================================================

/** Litz wire specification for high-frequency applications */
export interface LitzWireSpec {
    wire_type: 'litz'
    strand_awg: number
    strand_diameter_mm: number
    strand_count: number
    bundle_arrangement: string
    outer_diameter_mm: number
    total_area_cm2: number
    total_area_mm2: number
    Rdc_mOhm_per_m: number
    ac_factor: number
    skin_depth_mm: number
    effective_at_frequency: boolean
    loss_per_m_W?: number | null
    notes: string
}

/** Solid wire specification */
export interface SolidWireSpec {
    wire_type: 'solid'
    awg: number
    diameter_mm: number
    area_cm2: number
    strands: number
    skin_effect_limited: boolean
    skin_depth_mm: number
}

export type WireSpec = LitzWireSpec | SolidWireSpec

export interface WindingDesign {
    // Primary winding
    primary_turns: number
    primary_wire_awg: number
    primary_wire_dia_mm: number
    primary_strands: number
    primary_layers: number
    primary_Rdc_mOhm: number
    primary_Rac_Rdc: number
    primary_wire_type?: WireType
    
    // Secondary winding
    secondary_turns: number
    secondary_wire_awg: number
    secondary_wire_dia_mm: number
    secondary_strands: number
    secondary_layers: number
    secondary_Rdc_mOhm: number
    secondary_Rac_Rdc: number
    secondary_wire_type?: WireType
    
    // Window utilization
    total_Ku: number
    Ku_status: StatusType
}

// ============================================================================
// Response Types - Analysis
// ============================================================================

export interface LossAnalysis {
    // Core losses
    core_loss_W: number
    core_loss_density_mW_cm3: number
    
    // Copper losses
    primary_copper_loss_W: number
    secondary_copper_loss_W: number
    total_copper_loss_W: number
    
    // Totals
    total_loss_W: number
    efficiency_percent: number
    
    // Loss ratio (optimal ≈ 1.0 for balanced design)
    Pfe_Pcu_ratio: number
}

export interface ThermalAnalysis {
    power_dissipation_density_W_cm2: number
    temperature_rise_C: number
    hotspot_temp_C: number
    thermal_margin_C: number
    thermal_status: StatusType
    cooling_recommendation: string
}

export interface VerificationStatus {
    electrical: StatusType
    mechanical: StatusType
    thermal: StatusType
    warnings: string[]
    errors: string[]
    recommendations: string[]
}

// ============================================================================
// Response Types - Alternatives and Suggestions
// ============================================================================

export interface AlternativeCore {
    part_number: string
    manufacturer: string
    geometry: string
    material: string
    Ap_cm4: number
    source: CoreSource
    datasheet_url?: string | null
}

export interface ValidationItem {
    our_value: number
    reference_value: number
    difference_percent: number
    status: StatusType | 'unknown'
    confidence: ConfidenceLevel
    unit: string
}

// ============================================================================
// Response Types - Main Results
// ============================================================================

export interface TransformerDesignResult {
    // Design method used
    design_method: string
    design_method_name: string
    calculated_Ap_cm4: number
    calculated_Kg_cm5: number | null
    optimal_Pfe_Pcu_ratio: number | null
    
    // Selected core
    core: CoreSelection
    alternative_cores: AlternativeCore[]
    
    // Winding design
    winding: WindingDesign
    
    // Electrical parameters
    turns_ratio: number
    magnetizing_inductance_uH: number | null
    leakage_inductance_uH: number | null
    
    // Analysis results
    losses: LossAnalysis
    thermal: ThermalAnalysis
    verification: VerificationStatus
    validation: Record<string, ValidationItem> | null
    
    // Summary
    design_viable: boolean
    confidence_score: number
}

// ============================================================================
// No-Match Response Types
// ============================================================================

export interface DesignSuggestion {
    parameter: string
    current_value: number
    suggested_value: number
    unit: string
    impact: string
    feasible: boolean
}

export interface CoreAlternative {
    part_number: string
    manufacturer: string
    geometry: string
    Ap_cm4: number
    max_power_W: number
    notes: string
}

export interface NoMatchResult {
    success: false
    message: string
    required_Ap_cm4: number
    available_max_Ap_cm4: number
    suggestions: DesignSuggestion[]
    closest_cores: CoreAlternative[]
    alternative_approaches: string[]
}

// ============================================================================
// Type Guards
// ============================================================================

/** Type guard to check if response is a successful design result */
export function isDesignResult(data: unknown): data is TransformerDesignResult {
    return (
        typeof data === 'object' &&
        data !== null &&
        'design_viable' in data &&
        'core' in data &&
        'winding' in data &&
        !('suggestions' in data && (data as NoMatchResult).success === false)
    )
}

/** Type guard to check if response is a no-match suggestion result */
export function isNoMatchResult(data: unknown): data is NoMatchResult {
    return (
        typeof data === 'object' &&
        data !== null &&
        'success' in data &&
        (data as NoMatchResult).success === false &&
        'suggestions' in data
    )
}

/** Type guard to check if wire spec is Litz wire */
export function isLitzWire(wire: WireSpec): wire is LitzWireSpec {
    return wire.wire_type === 'litz'
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE = 'http://127.0.0.1:8000'

// ============================================================================
// Composable
// ============================================================================

export function useTransformerDesign() {
    const loading = ref(false)
    const error = ref<string | null>(null)
    const result = ref<TransformerDesignResult | null>(null)
    const suggestions = ref<NoMatchResult | null>(null)

    const requirements = ref<TransformerRequirements>({
        output_power_W: 2200,
        primary_voltage_V: 400,
        secondary_voltage_V: 250,
        frequency_Hz: 100050,
        efficiency_percent: 90,
        regulation_percent: 5,
        ambient_temp_C: 40,
        max_temp_rise_C: 50,
        cooling: 'natural',
        design_method: 'kgfe_erickson',
        max_current_density_A_cm2: 400,
        window_utilization_Ku: 0.35,
        waveform: 'square',
    })

    async function designTransformer(): Promise<void> {
        loading.value = true
        error.value = null
        result.value = null
        suggestions.value = null

        try {
            const response = await fetch(`${API_BASE}/api/design/transformer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requirements.value),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }

            const data: unknown = await response.json()

            // Use type guards for safe type checking
            if (isNoMatchResult(data)) {
                suggestions.value = data
                result.value = null
            } else if (isDesignResult(data)) {
                result.value = data
                suggestions.value = null
            } else {
                throw new Error('Unexpected response format from API')
            }
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Unknown error occurred'
        } finally {
            loading.value = false
        }
    }

    function applySuggestion(suggestion: DesignSuggestion): void {
        // Apply the suggested value to requirements with proper type handling
        const param = suggestion.parameter as keyof TransformerRequirements
        
        // Type-safe mapping of numeric parameters
        const numericParams: (keyof TransformerRequirements)[] = [
            'output_power_W',
            'efficiency_percent',
            'regulation_percent',
            'primary_voltage_V',
            'secondary_voltage_V',
            'frequency_Hz',
            'duty_cycle',
            'ambient_temp_C',
            'max_temp_rise_C',
            'max_current_density_A_cm2',
            'window_utilization_Ku',
        ]
        
        if (numericParams.includes(param) && typeof suggestion.suggested_value === 'number') {
            // Safe assignment for numeric parameters
            ;(requirements.value as Record<string, number>)[param] = suggestion.suggested_value
        }
    }

    function reset(): void {
        result.value = null
        suggestions.value = null
        error.value = null
    }

    /** Export design to various formats (placeholder for future implementation) */
    async function exportDesign(format: 'mas' | 'pdf' | 'json'): Promise<Blob | null> {
        if (!result.value) {
            error.value = 'No design to export'
            return null
        }
        
        // TODO: Implement export endpoints
        console.log(`Export to ${format} not yet implemented`)
        return null
    }

    return {
        // State
        requirements,
        loading,
        error,
        result,
        suggestions,
        
        // Actions
        designTransformer,
        applySuggestion,
        reset,
        exportDesign,
    }
}

