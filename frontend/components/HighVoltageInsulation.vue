<template>
  <div class="insulation-input-container">
    <div class="grid grid-2 gap-4">

      <!-- Inputs -->
      <div class="inputs">
        <div class="form-group mb-2">
            <label>Isolation Voltage [Vrms]</label>
            <input type="number" v-model.number="localVoltage" @input="emitUpdate" min="100">
        </div>

        <div class="form-group mb-2">
            <label>Insulation Type</label>
            <select v-model="localType" @change="emitUpdate">
                <option value="functional">Functional</option>
                <option value="basic">Basic</option>
                <option value="supplementary">Supplementary</option>
                <option value="double">Double</option>
                <option value="reinforced">Reinforced</option>
            </select>
        </div>

        <div class="grid grid-2 gap-2">
            <div class="form-group mb-2">
                <label>Pollution Degree</label>
                <select v-model.number="localPollution" @change="emitUpdate">
                    <option value="1">1 (Clean/Dry)</option>
                    <option value="2">2 (Typical Office)</option>
                    <option value="3">3 (Industrial)</option>
                </select>
            </div>
            <div class="form-group mb-2">
                <label>Overvoltage Cat.</label>
                <select v-model="localOvervoltage" @change="emitUpdate">
                    <option value="I">I (Signal)</option>
                    <option value="II">II (Appliance)</option>
                    <option value="III">III (Industrial)</option>
                </select>
            </div>
        </div>

        <div class="form-group mb-2">
            <label>Material Group</label>
             <select v-model="localMaterialGroup" @change="emitUpdate">
                <option value="I">I (CTI ≥ 600)</option>
                <option value="II">II (400 ≤ CTI < 600)</option>
                <option value="IIIa">IIIa (175 ≤ CTI < 400)</option>
                <option value="IIIb">IIIb (100 ≤ CTI < 175)</option>
            </select>
        </div>
      </div>

      <!-- Visualization -->
      <div class="visualization">
         <div class="diagram-container">
             <svg viewBox="0 0 200 120" class="insulation-svg">
                 <!-- PCB / Surface -->
                 <rect x="10" y="80" width="180" height="10" fill="#333" />

                 <!-- Primary Pad -->
                 <rect x="30" y="70" width="30" height="10" fill="#f59e0b" />
                 <text x="45" y="65" text-anchor="middle" font-size="8" fill="#aaa">PRI</text>

                 <!-- Secondary Pad -->
                 <rect x="140" y="70" width="30" height="10" fill="#f59e0b" />
                 <text x="155" y="65" text-anchor="middle" font-size="8" fill="#aaa">SEC</text>

                 <!-- Creepage Path -->
                 <path d="M 60 80 L 140 80" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 2" />
                 <text x="100" y="95" text-anchor="middle" font-size="9" fill="#ef4444">Creepage</text>

                 <!-- Clearance Path -->
                 <path d="M 60 70 Q 100 40 140 70" stroke="#3b82f6" stroke-width="2" fill="none" />
                 <text x="100" y="50" text-anchor="middle" font-size="9" fill="#3b82f6">Clearance</text>
             </svg>
         </div>

         <!-- Live Estimation (Simplified) -->
         <div class="estimations mt-2">
             <div class="est-row">
                 <span class="dot clearance"></span>
                 <span>Min Clearance:</span>
                 <strong>~{{ estimatedClearance }} mm</strong>
             </div>
             <div class="est-row">
                 <span class="dot creepage"></span>
                 <span>Min Creepage:</span>
                 <strong>~{{ estimatedCreepage }} mm</strong>
             </div>
             <small class="note">Actual values calculated by server</small>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  modelValue: any // Requirements
}>()

const emit = defineEmits(['update:modelValue'])

const localVoltage = ref(props.modelValue.isolation_voltage_Vrms || 1500)
const localType = ref(props.modelValue.insulation_type || 'basic')
const localPollution = ref(props.modelValue.pollution_degree || 2)
const localOvervoltage = ref(props.modelValue.overvoltage_category || 'II')
const localMaterialGroup = ref('II') // Not currently in main requirements interface, might need to add or keep local

watch(() => props.modelValue, (newVal) => {
    localVoltage.value = newVal.isolation_voltage_Vrms
    localType.value = newVal.insulation_type
    localPollution.value = newVal.pollution_degree
    localOvervoltage.value = newVal.overvoltage_category
}, { deep: true })

function emitUpdate() {
    emit('update:modelValue', {
        ...props.modelValue,
        isolation_voltage_Vrms: localVoltage.value,
        insulation_type: localType.value,
        pollution_degree: localPollution.value,
        overvoltage_category: localOvervoltage.value,
        // Material group is likely used for creepage calc but might not be in the top-level request object yet
    })
}

// Very rough client-side estimation for immediate feedback
// Real calculation happens on backend
const estimatedClearance = computed(() => {
    // IEC 60664-1 Table F.2 simplified
    // 1.5kV -> ~1.5mm, 3kV -> ~3mm roughly for basic
    let base = localVoltage.value / 1000.0
    if (localType.value === 'reinforced') base *= 2
    return base.toFixed(1)
})

const estimatedCreepage = computed(() => {
    // IEC 60664-1 Table F.4
    // Pollution degree multiplier
    let factor = 1.0
    if (localPollution.value === 2) factor = 1.0
    if (localPollution.value === 3) factor = 1.2

    let base = (localVoltage.value / 1000.0) * 2 // Approx 2mm/kV for generic PCB
    if (localType.value === 'reinforced') base *= 2
    return (base * factor).toFixed(1)
})
</script>

<style scoped>
.insulation-input-container {
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-sm);
    padding: 1rem;
    border: 1px solid var(--color-border);
}

.visualization {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #111;
    border-radius: var(--radius-sm);
    padding: 1rem;
}

.insulation-svg {
    width: 100%;
    height: 120px;
}

.estimations {
    width: 100%;
    margin-top: 1rem;
    padding-top: 0.5rem;
    border-top: 1px solid #333;
}

.est-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
}

.dot.clearance { background: #3b82f6; }
.dot.creepage { background: #ef4444; }

.note {
    display: block;
    text-align: center;
    color: #666;
    font-size: 0.7rem;
    margin-top: 0.5rem;
}
</style>
