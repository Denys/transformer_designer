<template>
    <div class="page-container">
        <div class="page-header">
            <h1>🔌 Pulse Transformer Designer</h1>
            <p class="subtitle">HV Power Pulse & Gate Drive Transformers</p>
        </div>

        <div class="grid grid-2 gap-6">
            <!-- Input Section -->
            <div class="card">
                <h3>Design Requirements</h3>
                
                <!-- Application Mode -->
                <div class="form-section">
                    <h4>Application Mode</h4>
                    <div class="button-group">
                        <button 
                            :class="['btn', requirements.application === 'hv_power_pulse' ? 'btn-primary' : 'btn-secondary']"
                            @click="setHvPowerPulseMode">
                            ⚡ HV Power Pulse
                        </button>
                        <button 
                            :class="['btn', requirements.application === 'gate_drive' ? 'btn-primary' : 'btn-secondary']"
                            @click="requirements.application = 'gate_drive'">
                            🎛️ Gate Drive
                        </button>
                    </div>
                    <div v-if="requirements.application === 'hv_power_pulse'" class="info-box mt-3">
                        💡 HV Power Pulse mode uses silicon-steel cores (Bmax ~1.2T) for energy transfer applications like plasma power supplies.
                    </div>
                </div>

                <form @submit.prevent="designPulseTransformer">
                    <!-- Voltage -->
                    <div class="form-section">
                        <h4>Voltages</h4>
                        <div class="grid grid-2 gap-3">
                            <div class="form-group">
                                <label>Primary Voltage [V]</label>
                                <input type="number" v-model.number="requirements.primary_voltage_V" min="1" required>
                            </div>
                            <div class="form-group">
                                <label>Secondary Voltage [V]</label>
                                <input type="number" v-model.number="requirements.secondary_voltage_V" min="1" required>
                            </div>
                        </div>
                        <div class="ratio-display">
                            Turns ratio: {{ (requirements.secondary_voltage_V / requirements.primary_voltage_V).toFixed(1) }}:1
                        </div>
                    </div>

                    <!-- Pulse Parameters -->
                    <div class="form-section">
                        <h4>Pulse Parameters</h4>
                        <div class="grid grid-2 gap-3">
                            <div class="form-group">
                                <label>Pulse Width [µs]</label>
                                <input type="number" v-model.number="requirements.pulse_width_us" min="0.1" step="0.1" required>
                                <small v-if="requirements.pulse_width_us > 1000">= {{ (requirements.pulse_width_us / 1000).toFixed(2) }} ms</small>
                            </div>
                            <div class="form-group">
                                <label>Frequency [Hz]</label>
                                <input type="number" v-model.number="requirements.frequency_Hz" min="1" required>
                            </div>
                            <div class="form-group">
                                <label>Peak Current [A]</label>
                                <input type="number" v-model.number="requirements.peak_current_A" min="0.001" step="0.1">
                            </div>
                            <div class="form-group">
                                <label>Duty Cycle [%]</label>
                                <input type="number" v-model.number="requirements.duty_cycle_percent" min="0.1" max="99" step="0.1">
                            </div>
                        </div>
                    </div>

                    <!-- Turns (for HV Power Pulse) -->
                    <div class="form-section" v-if="requirements.application === 'hv_power_pulse'">
                        <h4>Winding Turns</h4>
                        <div class="grid grid-2 gap-3">
                            <div class="form-group">
                                <label>Primary Turns</label>
                                <input type="number" v-model.number="requirements.primary_turns" min="1" max="100">
                            </div>
                            <div class="form-group">
                                <label>Secondary Turns</label>
                                <input type="number" v-model.number="requirements.secondary_turns" min="1" max="1000">
                            </div>
                        </div>
                    </div>

                    <!-- Insulation -->
                    <div class="form-section">
                        <h4>Insulation (IEC 60664)</h4>
                        <div class="grid grid-2 gap-3">
                            <div class="form-group">
                                <label>Isolation Voltage [Vrms]</label>
                                <input type="number" v-model.number="requirements.isolation_voltage_Vrms" min="100" required>
                            </div>
                            <div class="form-group">
                                <label>Insulation Type</label>
                                <select v-model="requirements.insulation_type">
                                    <option value="functional">Functional</option>
                                    <option value="basic">Basic</option>
                                    <option value="supplementary">Supplementary</option>
                                    <option value="double">Double</option>
                                    <option value="reinforced">Reinforced</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Core Material Type -->
                    <div class="form-section">
                        <h4>Core Material</h4>
                        <select v-model="requirements.core_material_type" class="full-width">
                            <option value="ferrite">Ferrite (HF, Bmax ~0.2T)</option>
                            <option value="silicon_steel">Silicon Steel (LF, Bmax ~1.2T)</option>
                            <option value="amorphous">Amorphous (Bmax ~1.0T)</option>
                            <option value="nanocrystalline">Nanocrystalline (Bmax ~0.8T)</option>
                        </select>
                    </div>

                    <!-- Submit -->
                    <button type="submit" class="btn btn-primary btn-lg full-width" :disabled="loading">
                        <span v-if="loading" class="spinner"></span>
                        <span v-else>⚡ Design Pulse Transformer</span>
                    </button>
                </form>
            </div>

            <!-- Results Section -->
            <div class="card" v-if="result || error">
                <h3>Design Results</h3>

                <!-- Error -->
                <div v-if="error" class="error-box">
                    <strong>Error:</strong> {{ error }}
                </div>

                <!-- Results -->
                <div v-if="result">
                    <!-- Core -->
                    <div class="result-section">
                        <h4>🧲 Core Selection</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <span class="label">Part Number</span>
                                <span class="value">{{ result.core.part_number }}</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Geometry</span>
                                <span class="value">{{ result.core.geometry }}</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Ae</span>
                                <span class="value">{{ result.core.Ae_cm2.toFixed(3) }} cm²</span>
                            </div>
                            <div class="result-item">
                                <span class="label">V·t</span>
                                <span class="value">{{ result.volt_second_uVs.toFixed(0) }} V·µs</span>
                            </div>
                        </div>
                    </div>

                    <!-- Windings -->
                    <div class="result-section">
                        <h4>🔄 Winding Design</h4>
                        <div class="grid grid-2 gap-3">
                            <div class="winding-box">
                                <strong>Primary</strong>
                                <div>Turns: <b>{{ result.primary.turns }}</b></div>
                                <div>Wire: <b>{{ result.primary.wire_type }}</b> 
                                    <span v-if="result.primary.wire_awg">AWG {{ result.primary.wire_awg }}</span>
                                </div>
                                <div>Area: <b>{{ result.primary.wire_area_mm2 }} mm²</b></div>
                                <div>Ipeak: <b>{{ result.primary.peak_current_A }} A</b></div>
                            </div>
                            <div class="winding-box">
                                <strong>Secondary</strong>
                                <div>Turns: <b>{{ result.secondary.turns }}</b></div>
                                <div>Wire: <b>{{ result.secondary.wire_type }}</b>
                                    <span v-if="result.secondary.wire_awg">AWG {{ result.secondary.wire_awg }}</span>
                                </div>
                                <div>Area: <b>{{ result.secondary.wire_area_mm2 }} mm²</b></div>
                            </div>
                        </div>
                        <div class="ratio-display mt-3">
                            Actual ratio: {{ result.turns_ratio.toFixed(2) }}:1 
                            ({{ result.primary.turns }}:{{ result.secondary.turns }})
                        </div>
                    </div>

                    <!-- Pulse Response -->
                    <div class="result-section">
                        <h4>📊 Pulse Response</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <span class="label">Rise Time</span>
                                <span class="value">{{ result.pulse_response.rise_time_ns.toFixed(1) }} ns</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Droop</span>
                                <span class="value" :class="{'warning': result.pulse_response.droop_percent > 10}">
                                    {{ result.pulse_response.droop_percent.toFixed(2) }}%
                                </span>
                            </div>
                            <div class="result-item">
                                <span class="label">Backswing</span>
                                <span class="value">{{ result.pulse_response.backswing_percent.toFixed(1) }}%</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Bandwidth</span>
                                <span class="value">{{ result.pulse_response.bandwidth_3dB_MHz.toFixed(2) }} MHz</span>
                            </div>
                        </div>
                    </div>

                    <!-- Insulation Requirements -->
                    <div class="result-section">
                        <h4>🛡️ Insulation (IEC 60664)</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <span class="label">Clearance</span>
                                <span class="value">{{ result.insulation.clearance_mm.toFixed(1) }} mm</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Creepage</span>
                                <span class="value">{{ result.insulation.creepage_mm.toFixed(1) }} mm</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Solid Insulation</span>
                                <span class="value">{{ result.insulation.solid_insulation_mm.toFixed(2) }} mm</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Impulse Withstand</span>
                                <span class="value">{{ result.insulation.impulse_withstand_kV.toFixed(1) }} kV</span>
                            </div>
                        </div>
                        <div v-if="result.insulation.construction_notes.length > 0" class="notes mt-3">
                            <strong>Notes:</strong>
                            <ul>
                                <li v-for="note in result.insulation.construction_notes" :key="note">{{ note }}</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Thermal -->
                    <div class="result-section">
                        <h4>🌡️ Thermal Analysis</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <span class="label">Core Loss</span>
                                <span class="value">{{ result.thermal.core_loss_mW.toFixed(1) }} mW</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Copper Loss</span>
                                <span class="value">{{ result.thermal.copper_loss_mW.toFixed(1) }} mW</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Total Loss</span>
                                <span class="value">{{ result.thermal.total_loss_mW.toFixed(1) }} mW</span>
                            </div>
                            <div class="result-item">
                                <span class="label">Temp Rise</span>
                                <span class="value" :class="{'warning': result.thermal.temperature_rise_C > 50}">
                                    {{ result.thermal.temperature_rise_C.toFixed(1) }}°C
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Verification -->
                    <div class="result-section" v-if="result.verification">
                        <h4 :class="result.verification.meets_specifications ? 'success' : 'warning'">
                            {{ result.verification.meets_specifications ? '✅ Meets Specs' : '⚠️ Review Needed' }}
                        </h4>
                        <div v-if="result.verification.warnings.length > 0" class="warning-list">
                            <div v-for="w in result.verification.warnings" :key="w" class="warning-item">
                                ⚠️ {{ w }}
                            </div>
                        </div>
                        <div v-if="result.verification.recommendations.length > 0" class="recommendation-list">
                            <div v-for="r in result.verification.recommendations" :key="r" class="recommendation-item">
                                💡 {{ r }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { usePulseDesign } from '~/composables/usePulseDesign'

const { 
    requirements, 
    loading, 
    error, 
    result, 
    designPulseTransformer, 
    setHvPowerPulseMode 
} = usePulseDesign()
</script>

<style scoped>
.page-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

.page-header {
    text-align: center;
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: var(--color-accent-primary);
}

.subtitle {
    color: var(--color-text-muted);
}

.card {
    background: var(--color-bg-secondary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
}

.form-section {
    margin-bottom: 1.5rem;
}

.form-section h4 {
    font-size: 0.9rem;
    color: var(--color-accent-primary);
    margin-bottom: 0.75rem;
    border-bottom: 1px solid var(--color-border);
    padding-bottom: 0.5rem;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-group label {
    font-size: 0.8rem;
    color: var(--color-text-muted);
    margin-bottom: 0.25rem;
}

.form-group input,
.form-group select {
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-bg-tertiary);
    color: var(--color-text-primary);
}

.form-group small {
    font-size: 0.7rem;
    color: var(--color-accent-secondary);
    margin-top: 0.25rem;
}

.button-group {
    display: flex;
    gap: 0.5rem;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}

.btn-primary {
    background: var(--color-accent-primary);
    color: white;
}

.btn-secondary {
    background: var(--color-bg-tertiary);
    color: var(--color-text-secondary);
}

.btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
}

.full-width {
    width: 100%;
}

.info-box {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid var(--color-info);
    border-radius: var(--radius-sm);
    padding: 0.75rem;
    font-size: 0.85rem;
    color: var(--color-text-secondary);
}

.error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--color-error);
    border-radius: var(--radius-sm);
    padding: 0.75rem;
    color: var(--color-error);
}

.ratio-display {
    font-size: 0.85rem;
    color: var(--color-text-muted);
    margin-top: 0.5rem;
    text-align: center;
}

.result-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--color-border);
}

.result-section:last-child {
    border-bottom: none;
}

.result-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
}

.result-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-sm);
}

.result-item .label {
    color: var(--color-text-muted);
    font-size: 0.85rem;
}

.result-item .value {
    font-weight: 600;
    color: var(--color-text-primary);
}

.result-item .value.warning {
    color: var(--color-warning);
}

.winding-box {
    padding: 0.75rem;
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
}

.winding-box strong {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--color-accent-primary);
}

.warning-list, .recommendation-list {
    margin-top: 0.75rem;
}

.warning-item, .recommendation-item {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
}

.warning-item {
    background: rgba(245, 158, 11, 0.1);
    color: var(--color-warning);
}

.recommendation-item {
    background: rgba(59, 130, 246, 0.1);
    color: var(--color-info);
}

.notes {
    font-size: 0.85rem;
    color: var(--color-text-secondary);
}

.notes ul {
    margin: 0.5rem 0 0 1.5rem;
    padding: 0;
}

.success {
    color: var(--color-success);
}

.warning {
    color: var(--color-warning);
}

.spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid white;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.grid {
    display: grid;
}

.grid-2 {
    grid-template-columns: repeat(2, 1fr);
}

.gap-3 {
    gap: 0.75rem;
}

.gap-6 {
    gap: 1.5rem;
}

.mt-3 {
    margin-top: 0.75rem;
}
</style>
