/**
 * Composable for pulse transformer design API interactions
 * Supports both gate-drive and HV power pulse (like Dropless) applications
 */

// ============================================================================
// Types
// ============================================================================

export type PulseApplicationType =
    | 'gate_drive'
    | 'signal_isolation'
    | 'trigger'
    | 'hv_pulse'
    | 'hv_power_pulse'  // High-voltage high-current energy transfer
    | 'ethernet'
    | 'telecom'
    | 'custom'

export type InsulationType = 'functional' | 'basic' | 'supplementary' | 'double' | 'reinforced'
export type OvervoltageCategory = 'I' | 'II' | 'III' | 'IV'
export type PollutionDegree = 1 | 2 | 3
export type CoreMaterialType = 'ferrite' | 'silicon_steel' | 'amorphous' | 'nanocrystalline'

export interface PulseTransformerRequirements {
    application: PulseApplicationType

    // Voltage specifications
    primary_voltage_V: number
    secondary_voltage_V: number

    // Pulse specifications
    pulse_width_us: number
    pulse_width_ms?: number  // For millisecond-range pulses
    rise_time_ns?: number
    duty_cycle_percent: number
    frequency_Hz: number

    // Load specifications
    load_resistance_ohm?: number
    load_capacitance_pF?: number
    peak_current_A?: number

    // Energy-mode parameters (for HV_POWER_PULSE)
    primary_capacitance_uF?: number
    secondary_capacitance_uF?: number
    energy_per_pulse_J?: number

    // Performance requirements
    max_droop_percent: number
    max_backswing_percent: number

    // Isolation requirements
    isolation_voltage_Vrms: number
    insulation_type: InsulationType
    overvoltage_category: OvervoltageCategory
    pollution_degree: PollutionDegree

    // Thermal
    ambient_temp_C: number
    max_temp_rise_C: number

    // Design preferences
    preferred_core_geometry?: string
    preferred_material?: string
    core_material_type?: CoreMaterialType

    // Direct turns specification (for HV power pulse)
    primary_turns?: number
    secondary_turns?: number
}

export interface PulseTransformerResult {
    application: string
    volt_second_uVs: number
    turns_ratio: number

    core: {
        part_number: string
        manufacturer: string
        geometry: string
        material: string
        Ae_cm2: number
        Ap_cm4: number
        source: string
    }

    primary: {
        turns: number
        wire_type: string
        wire_awg: number | null
        wire_diameter_mm: number
        wire_area_mm2: number
        peak_current_A: number
        layers: number
        Rdc_mOhm: number
        inductance_uH: number
    }

    secondary: {
        turns: number
        wire_type: string
        wire_awg: number | null
        wire_diameter_mm: number
        wire_area_mm2: number
        layers: number
        Rdc_mOhm: number
    }

    electrical: {
        magnetizing_inductance_uH: number
        leakage_inductance_nH: number
        interwinding_capacitance_pF: number
    }

    pulse_response: {
        rise_time_ns: number
        fall_time_ns: number
        droop_percent: number
        backswing_percent: number
        bandwidth_3dB_MHz: number
        ringing_freq_MHz: number | null
        overshoot_percent: number
    }

    insulation: {
        clearance_mm: number
        creepage_mm: number
        solid_insulation_mm: number
        impulse_withstand_kV: number
        recommended_materials: string[]
        construction_notes: string[]
    }

    thermal: {
        core_loss_mW: number
        copper_loss_mW: number
        total_loss_mW: number
        temperature_rise_C: number
    }

    verification: {
        meets_specifications: boolean
        warnings: string[]
        recommendations: string[]
    }
}

export interface GateDriverPreset {
    name: string
    description: string
    device_type: string
    typical_Vdrive: number
    typical_Ipeak: number
    typical_Qg_nC: number
    typical_ton_ns: number
    typical_toff_ns: number
    suggested_turns_ratio: number
    suggested_Lm_min_uH: number
    suggested_Llk_max_nH: number
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE = 'http://127.0.0.1:8000'

// ============================================================================
// Composable
// ============================================================================

export function usePulseDesign() {
    const loading = ref(false)
    const error = ref<string | null>(null)
    const result = ref<PulseTransformerResult | null>(null)
    const presets = ref<Record<string, GateDriverPreset>>({})

    const requirements = ref<PulseTransformerRequirements>({
        application: 'hv_power_pulse',  // Default to HV power pulse (like Dropless)

        // Dropless-style specs as defaults
        primary_voltage_V: 200,
        secondary_voltage_V: 3500,
        pulse_width_us: 2500,  // 2.5ms
        duty_cycle_percent: 31.25,  // 125Hz × 2.5ms
        frequency_Hz: 125,
        peak_current_A: 1750,

        max_droop_percent: 10,
        max_backswing_percent: 20,

        isolation_voltage_Vrms: 4000,
        insulation_type: 'reinforced',
        overvoltage_category: 'II',
        pollution_degree: 2,

        ambient_temp_C: 25,
        max_temp_rise_C: 50,

        core_material_type: 'silicon_steel',
        primary_turns: 2,
        secondary_turns: 50,
    })

    async function designPulseTransformer(): Promise<void> {
        loading.value = true
        error.value = null
        result.value = null

        try {
            const response = await fetch(`${API_BASE}/api/design/pulse/design`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requirements.value),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }

            result.value = await response.json()
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Unknown error occurred'
        } finally {
            loading.value = false
        }
    }

    async function loadPresets(): Promise<void> {
        try {
            const response = await fetch(`${API_BASE}/api/design/pulse/presets`)
            if (response.ok) {
                const data = await response.json()
                presets.value = data.presets || {}
            }
        } catch (e) {
            console.error('Failed to load presets:', e)
        }
    }

    function applyPreset(presetKey: string): void {
        const preset = presets.value[presetKey]
        if (preset) {
            requirements.value.application = 'gate_drive'
            requirements.value.primary_voltage_V = preset.typical_Vdrive
            requirements.value.secondary_voltage_V = preset.typical_Vdrive
            requirements.value.peak_current_A = preset.typical_Ipeak
            requirements.value.rise_time_ns = preset.typical_ton_ns
            requirements.value.core_material_type = 'ferrite'
        }
    }

    function setHvPowerPulseMode(): void {
        // Set to Dropless-style HV power pulse defaults
        requirements.value.application = 'hv_power_pulse'
        requirements.value.core_material_type = 'silicon_steel'
        requirements.value.primary_voltage_V = 200
        requirements.value.secondary_voltage_V = 3500
        requirements.value.pulse_width_us = 2500
        requirements.value.frequency_Hz = 125
        requirements.value.peak_current_A = 1750
        requirements.value.isolation_voltage_Vrms = 4000
        requirements.value.insulation_type = 'reinforced'
        requirements.value.primary_turns = 2
        requirements.value.secondary_turns = 50
    }

    function reset(): void {
        result.value = null
        error.value = null
    }

    return {
        requirements,
        loading,
        error,
        result,
        presets,

        designPulseTransformer,
        loadPresets,
        applyPreset,
        setHvPowerPulseMode,
        reset,
    }
}
