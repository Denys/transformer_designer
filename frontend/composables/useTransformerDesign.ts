/**
 * Composable for transformer design API interactions
 */

export interface TransformerRequirements {
    output_power_W: number
    efficiency_percent?: number
    regulation_percent?: number
    primary_voltage_V: number
    secondary_voltage_V: number
    frequency_Hz: number
    waveform?: 'sinusoidal' | 'square' | 'triangular'
    duty_cycle?: number
    ambient_temp_C?: number
    max_temp_rise_C?: number
    cooling?: 'natural' | 'forced'
    preferred_core_geometry?: string
    preferred_material?: string
    max_current_density_A_cm2?: number
    window_utilization_Ku?: number
}

export interface CoreSelection {
    manufacturer: string
    part_number: string
    geometry: string
    material: string
    Ae_cm2: number
    Wa_cm2: number
    Ap_cm4: number
    MLT_cm: number
    lm_cm: number
    Ve_cm3: number
    At_cm2: number
    weight_g: number
    Bsat_T: number
    Bmax_T: number
    mu_i: number
    source?: 'local' | 'openmagnetics'
    datasheet_url?: string | null
}

export interface WindingDesign {
    primary_turns: number
    primary_wire_awg: number
    primary_wire_dia_mm: number
    primary_strands: number
    primary_layers: number
    primary_Rdc_mOhm: number
    primary_Rac_Rdc: number
    secondary_turns: number
    secondary_wire_awg: number
    secondary_wire_dia_mm: number
    secondary_strands: number
    secondary_layers: number
    secondary_Rdc_mOhm: number
    secondary_Rac_Rdc: number
    total_Ku: number
    Ku_status: 'ok' | 'warning' | 'error'
}

export interface LossAnalysis {
    core_loss_W: number
    core_loss_density_mW_cm3: number
    primary_copper_loss_W: number
    secondary_copper_loss_W: number
    total_copper_loss_W: number
    total_loss_W: number
    efficiency_percent: number
    Pfe_Pcu_ratio: number
}

export interface ThermalAnalysis {
    power_dissipation_density_W_cm2: number
    temperature_rise_C: number
    hotspot_temp_C: number
    thermal_margin_C: number
    thermal_status: 'pass' | 'warning' | 'fail'
    cooling_recommendation: string
}

export interface VerificationStatus {
    electrical: 'pass' | 'warning' | 'fail'
    mechanical: 'pass' | 'warning' | 'fail'
    thermal: 'pass' | 'warning' | 'fail'
    warnings: string[]
    errors: string[]
    recommendations: string[]
}

export interface TransformerDesignResult {
    design_method: 'Ap' | 'Kg'
    calculated_Ap_cm4: number
    calculated_Kg_cm5: number | null
    core: CoreSelection
    winding: WindingDesign
    turns_ratio: number
    magnetizing_inductance_uH: number | null
    leakage_inductance_uH: number | null
    losses: LossAnalysis
    thermal: ThermalAnalysis
    verification: VerificationStatus
    design_viable: boolean
    confidence_score: number
}

// New suggestion types
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

const API_BASE = 'http://127.0.0.1:8000'

export function useTransformerDesign() {
    const loading = ref(false)
    const error = ref<string | null>(null)
    const result = ref<TransformerDesignResult | null>(null)
    const suggestions = ref<NoMatchResult | null>(null)

    const requirements = ref<TransformerRequirements>({
        output_power_W: 100,
        primary_voltage_V: 48,
        secondary_voltage_V: 12,
        frequency_Hz: 100000,
        efficiency_percent: 90,
        regulation_percent: 5,
        ambient_temp_C: 40,
        max_temp_rise_C: 50,
        cooling: 'natural',
        max_current_density_A_cm2: 400,
        window_utilization_Ku: 0.35,
        waveform: 'sinusoidal',
    })

    async function designTransformer() {
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
                const errData = await response.json()
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }

            const data = await response.json()

            // Check if this is a suggestions response or a design result
            if (data.success === false && data.suggestions) {
                // This is a NoMatchResult with suggestions
                suggestions.value = data as NoMatchResult
                result.value = null
            } else {
                // This is a successful design
                result.value = data as TransformerDesignResult
                suggestions.value = null
            }
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Unknown error'
        } finally {
            loading.value = false
        }
    }

    function applySuggestion(suggestion: DesignSuggestion) {
        // Apply the suggested value to requirements
        const param = suggestion.parameter as keyof TransformerRequirements
        if (param in requirements.value) {
            (requirements.value as any)[param] = suggestion.suggested_value
        }
    }

    function reset() {
        result.value = null
        suggestions.value = null
        error.value = null
    }

    return {
        requirements,
        loading,
        error,
        result,
        suggestions,
        designTransformer,
        applySuggestion,
        reset,
    }
}

