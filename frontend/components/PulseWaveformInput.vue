<template>
  <div class="waveform-input-container">
    <div class="grid grid-2 gap-4">
      <!-- Controls -->
      <div class="controls">
        <div class="form-group mb-3">
          <label>Waveform Type</label>
          <select v-model="localWaveformType" @change="emitUpdate">
            <option value="square">Square / Rectangular</option>
            <option value="capacitor_discharge">Capacitor Discharge</option>
            <option value="sinusoidal">Sinusoidal (Half-Sine)</option>
            <option value="triangular">Triangular</option>
          </select>
        </div>

        <div class="form-group mb-2">
          <label>Peak Voltage [V]</label>
          <input type="number" v-model.number="localVoltage" @input="emitUpdate" min="1">
        </div>

        <div class="form-group mb-2">
          <label>Pulse Width [µs]</label>
          <input type="number" v-model.number="localPulseWidthUs" @input="emitUpdate" min="0.1" step="0.1">
        </div>

        <div class="form-group mb-2">
          <label>Frequency [Hz]</label>
          <input type="number" v-model.number="localFrequency" @input="emitUpdate" min="1">
        </div>

        <!-- Capacitor Discharge Specifics -->
        <div v-if="localWaveformType === 'capacitor_discharge'" class="subsection p-2 mt-2">
          <small class="text-accent">Discharge Parameters</small>
          <div class="form-group mb-2 mt-2">
            <label>Capacitance [µF]</label>
            <input type="number" v-model.number="localCapacitanceUf" @input="emitUpdate" min="0.001" step="0.1">
          </div>
          <!--
            Note: Circuit resistance often comes from the load or winding.
            For now we might not ask it explicitly here if it's not in the main requirements object,
            but the backend model has it. The main design endpoint might assume load_resistance.
          -->
        </div>

        <!-- Rise/Fall Time (for Square/Pulse) -->
        <div v-if="localWaveformType === 'square' || localWaveformType === 'custom'" class="subsection p-2 mt-2">
           <div class="grid grid-2 gap-2">
             <div class="form-group">
               <label>Rise Time [ns]</label>
               <input type="number" v-model.number="localRiseTimeNs" @input="emitUpdate" min="0" step="10">
             </div>
             <div class="form-group">
               <label>Fall Time [ns]</label>
               <input type="number" v-model.number="localFallTimeNs" @input="emitUpdate" min="0" step="10">
             </div>
           </div>
        </div>

        <div class="stats mt-3">
          <div class="stat-item">
            <span>Period:</span>
            <strong>{{ (1000 / localFrequency).toFixed(2) }} ms</strong>
          </div>
          <div class="stat-item">
            <span>Duty Cycle:</span>
            <strong>{{ (localPulseWidthUs * 1e-6 * localFrequency * 100).toFixed(2) }}%</strong>
          </div>
          <div class="stat-item highlight">
             <span>Est. V·t:</span>
             <strong>{{ estimatedVoltSecond.toFixed(0) }} V·µs</strong>
          </div>
        </div>
      </div>

      <!-- Visualization -->
      <div class="visualization">
        <div class="waveform-preview">
          <svg viewBox="0 0 300 150" class="waveform-svg">
            <!-- Grid -->
            <defs>
              <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#333" stroke-width="0.5"/>
              </pattern>
            </defs>
            <rect width="300" height="150" fill="url(#grid)" />

            <!-- Axes -->
            <line x1="20" y1="130" x2="290" y2="130" stroke="#666" stroke-width="1" />
            <line x1="20" y1="10" x2="20" y2="130" stroke="#666" stroke-width="1" />

            <!-- Labels -->
            <text x="10" y="20" fill="#888" font-size="10">V</text>
            <text x="280" y="145" fill="#888" font-size="10">t</text>

            <!-- Waveform Path -->
            <path :d="waveformPath"
                  fill="rgba(59, 130, 246, 0.2)"
                  stroke="var(--color-accent-primary)"
                  stroke-width="2"
                  vector-effect="non-scaling-stroke"/>
          </svg>
        </div>
        <div class="legend mt-2">
            <small v-if="localWaveformType === 'capacitor_discharge'">
                Exponential decay: V(t) = V₀ · e^(-t/RC)
            </small>
            <small v-else-if="localWaveformType === 'sinusoidal'">
                Half-sine pulse
            </small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  modelValue: any // The requirements object
}>()

const emit = defineEmits(['update:modelValue'])

// Local state to avoid mutating props directly
const localWaveformType = ref('square')
const localVoltage = ref(props.modelValue.primary_voltage_V || 0)
const localPulseWidthUs = ref(props.modelValue.pulse_width_us || 0)
const localFrequency = ref(props.modelValue.frequency_Hz || 0)
const localRiseTimeNs = ref(props.modelValue.rise_time_ns || 0)
const localFallTimeNs = ref(props.modelValue.fall_time_ns || 0)
const localCapacitanceUf = ref(props.modelValue.primary_capacitance_uF || 0)

// Sync from props if they change externally
watch(() => props.modelValue, (newVal) => {
    localVoltage.value = newVal.primary_voltage_V
    localPulseWidthUs.value = newVal.pulse_width_us
    localFrequency.value = newVal.frequency_Hz
    localRiseTimeNs.value = newVal.rise_time_ns
    localFallTimeNs.value = newVal.fall_time_ns
    localCapacitanceUf.value = newVal.primary_capacitance_uF

    // Infer waveform type logic could go here if needed,
    // but we don't store waveform type in requirements object explicitly in the current interface
    // aside from implied usage. We might need to add it to requirements or just keep it local UI state.
}, { deep: true })

const estimatedVoltSecond = computed(() => {
    const v = localVoltage.value
    const t = localPulseWidthUs.value // microseconds

    if (localWaveformType.value === 'square') {
        return v * t
    } else if (localWaveformType.value === 'triangular') {
        return 0.5 * v * t
    } else if (localWaveformType.value === 'sinusoidal') {
        return (2/Math.PI) * v * t
    } else if (localWaveformType.value === 'capacitor_discharge') {
        // Rough estimate without R
        // Assuming significant discharge, area is less than square
        return v * t * 0.63 // (1-1/e) approx
    }
    return v * t
})

const waveformPath = computed(() => {
    // Generate SVG path d attribute
    // Canvas is 300x150. Origin at (20, 130). Max Height ~100px.
    // X scale: Let's make the pulse take up about 60-70% of the width for visibility

    const startX = 20
    const BaseY = 130
    const MaxH = 100

    const widthPx = 200 // Fixed width for visualization of "pulse width"

    // Rise/Fall scaling (only relevant for square/trapezoid)
    // rise is minimal compared to width usually
    const risePx = localWaveformType.value === 'square' ? Math.min(20, widthPx * 0.1) : 0
    const fallPx = localWaveformType.value === 'square' ? Math.min(20, widthPx * 0.1) : 0

    let d = `M ${startX} ${BaseY} `

    if (localWaveformType.value === 'square') {
        // Trapezoid
        d += `L ${startX + risePx} ${BaseY - MaxH} `
        d += `L ${startX + widthPx - fallPx} ${BaseY - MaxH} `
        d += `L ${startX + widthPx} ${BaseY} `
    } else if (localWaveformType.value === 'triangular') {
        d += `L ${startX + widthPx/2} ${BaseY - MaxH} `
        d += `L ${startX + widthPx} ${BaseY} `
    } else if (localWaveformType.value === 'sinusoidal') {
        // Quadratic bezier approximation for half sine
        // M start base, Q control end base
        d += `Q ${startX + widthPx/2} ${BaseY - MaxH * 1.5} ${startX + widthPx} ${BaseY} `
    } else if (localWaveformType.value === 'capacitor_discharge') {
        // Exponential decay curve
        // Start high, decay
        d += `L ${startX} ${BaseY - MaxH} ` // Jump to peak
        // Approximating exp decay with bezier or multiple lines
        // Point 1: 1/3 way, decay somewhat
        // Point 2: 2/3 way, decay more
        // End: Pulse width, decay to Vmin

        const cp1x = startX + widthPx * 0.33
        const cp1y = BaseY - MaxH * 0.7
        const cp2x = startX + widthPx * 0.66
        const cp2y = BaseY - MaxH * 0.4
        const endX = startX + widthPx
        const endY = BaseY - MaxH * 0.2 // Assume it doesn't go to zero in typical pulse

        d += `C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${endX} ${endY} `
        d += `L ${endX} ${BaseY} ` // Drop to zero at end of pulse width
    }

    return d
})

function emitUpdate() {
    emit('update:modelValue', {
        ...props.modelValue,
        primary_voltage_V: localVoltage.value,
        pulse_width_us: localPulseWidthUs.value,
        frequency_Hz: localFrequency.value,
        rise_time_ns: localRiseTimeNs.value,
        fall_time_ns: localFallTimeNs.value,
        primary_capacitance_uF: localCapacitanceUf.value
        // We might need to pass waveform type if we extend the backend API to accept it explicitly
    })
}
</script>

<style scoped>
.waveform-input-container {
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-sm);
    padding: 1rem;
    border: 1px solid var(--color-border);
}

.visualization {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #111;
    border-radius: var(--radius-sm);
    padding: 1rem;
}

.waveform-svg {
    width: 100%;
    height: 150px;
}

.stats {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 0.8rem;
    padding-top: 0.5rem;
    border-top: 1px solid var(--color-border);
}

.stat-item {
    display: flex;
    flex-direction: column;
}

.stat-item span {
    color: var(--color-text-muted);
}

.subsection {
    background: rgba(0,0,0,0.2);
    border-radius: var(--radius-sm);
}

.text-accent {
    color: var(--color-accent-secondary);
}

.highlight strong {
    color: var(--color-accent-primary);
}
</style>
