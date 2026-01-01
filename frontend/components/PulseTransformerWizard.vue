<template>
  <div class="pulse-transformer-wizard">
    <div class="steps flex justify-between mb-8">
      <div v-for="step in steps" :key="step.id"
           class="step flex-1 text-center py-2 border-b-2"
           :class="currentStep === step.id ? 'border-primary-500 font-bold' : 'border-gray-200 text-gray-500'">
        {{ step.name }}
      </div>
    </div>

    <div class="wizard-content p-6 bg-white rounded-lg shadow-sm border border-gray-200">
      <!-- Step 1: Application -->
      <div v-if="currentStep === 1">
        <h2 class="text-xl font-semibold mb-4">Application & Waveform</h2>
        <div class="grid grid-cols-1 gap-4">
          <!-- Application Type -->
          <div>
            <label class="block text-sm font-medium text-gray-700">Application Type</label>
            <select v-model="design.application" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
              <option value="gate_drive">Gate Drive</option>
              <option value="hv_power_pulse">HV Power Pulse (Energy Transfer)</option>
              <option value="signal_isolation">Signal Isolation</option>
            </select>
          </div>

          <!-- Waveform Params -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Primary Voltage (V)</label>
              <input type="number" v-model.number="design.primary_voltage_V" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Pulse Width (µs)</label>
              <input type="number" v-model.number="design.pulse_width_us" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Frequency (Hz)</label>
              <input type="number" v-model.number="design.frequency_Hz" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Duty Cycle (%)</label>
              <input type="number" v-model.number="design.duty_cycle_percent" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Load & Output -->
      <div v-else-if="currentStep === 2">
        <h2 class="text-xl font-semibold mb-4">Load & Output</h2>
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Secondary Voltage (V)</label>
            <input type="number" v-model.number="design.secondary_voltage_V" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
          </div>

          <div v-if="design.application === 'hv_power_pulse'">
             <div>
                <label class="block text-sm font-medium text-gray-700">Load Capacitance (µF)</label>
                <input type="number" v-model.number="design.secondary_capacitance_uF" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
             </div>
             <div>
                <label class="block text-sm font-medium text-gray-700">Primary Capacitance (µF)</label>
                <input type="number" v-model.number="design.primary_capacitance_uF" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
             </div>
          </div>
          <div v-else>
             <div class="grid grid-cols-2 gap-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700">Load Resistance (Ω)</label>
                  <input type="number" v-model.number="design.load_resistance_ohm" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700">Load Capacitance (pF)</label>
                  <input type="number" v-model.number="design.load_capacitance_pF" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
               </div>
             </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Constraints -->
      <div v-else-if="currentStep === 3">
        <h2 class="text-xl font-semibold mb-4">Constraints</h2>
        <div class="grid grid-cols-1 gap-4">
           <div>
              <label class="block text-sm font-medium text-gray-700">Isolation Voltage (Vrms)</label>
              <input type="number" v-model.number="design.isolation_voltage_Vrms" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
           </div>
           <div>
              <label class="block text-sm font-medium text-gray-700">Max Height (mm) (Optional)</label>
              <input type="number" v-model.number="design.max_height_mm" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm" />
           </div>
        </div>
      </div>

      <!-- Step 4: Review -->
      <div v-else-if="currentStep === 4">
        <h2 class="text-xl font-semibold mb-4">Review</h2>
        <div class="bg-gray-50 p-4 rounded text-sm">
           <pre>{{ JSON.stringify(design, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <div class="actions mt-6 flex justify-between">
      <button v-if="currentStep > 1" @click="currentStep--" class="px-4 py-2 border rounded hover:bg-gray-50">Back</button>
      <div v-else></div> <!-- Spacer -->

      <button v-if="currentStep < 4" @click="currentStep++" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Next</button>
      <button v-else @click="runDesign" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700" :disabled="loading">
        {{ loading ? 'Calculating...' : 'Run Design' }}
      </button>
    </div>

    <!-- Results Modal/Overlay -->
    <div v-if="result" class="results mt-8 p-6 bg-gray-50 border rounded-lg">
      <h3 class="text-xl font-bold mb-4">Design Results</h3>

      <div v-if="result.verification" class="mb-4 p-3 rounded"
           :class="result.verification.meets_specifications ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">
        <span class="font-bold">{{ result.verification.meets_specifications ? 'PASS' : 'FAIL' }}</span>
        <ul v-if="result.verification.warnings.length" class="mt-2 text-sm list-disc pl-5">
          <li v-for="w in result.verification.warnings" :key="w">{{ w }}</li>
        </ul>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <div>
          <h4 class="font-semibold text-gray-700">Core Selection</h4>
          <p class="text-lg">{{ result.core.part_number }}</p>
          <p class="text-sm text-gray-500">{{ result.core.manufacturer }} ({{ result.core.material }})</p>
          <p class="text-sm">Ae: {{ result.core.Ae_cm2 }} cm²</p>
        </div>
        <div>
          <h4 class="font-semibold text-gray-700">Winding</h4>
          <p>Primary: {{ result.primary.turns }} turns ({{ result.primary.wire_type }})</p>
          <p>Secondary: {{ result.secondary.turns }} turns ({{ result.secondary.wire_type }})</p>
        </div>
      </div>

      <div class="mt-6 flex justify-end">
         <button @click="result = null" class="px-4 py-2 text-gray-600 hover:text-gray-800">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';

const currentStep = ref(1);
const loading = ref(false);
const result = ref(null);
const steps = [
  { id: 1, name: 'Application' },
  { id: 2, name: 'Load' },
  { id: 3, name: 'Constraints' },
  { id: 4, name: 'Review' }
];

const design = reactive({
  application: 'gate_drive',
  primary_voltage_V: 15,
  secondary_voltage_V: 15,
  pulse_width_us: 1,
  frequency_Hz: 100000,
  duty_cycle_percent: 50,
  load_resistance_ohm: 10,
  load_capacitance_pF: 100,
  isolation_voltage_Vrms: 1500
});

const emit = defineEmits(['design-complete']);

const runDesign = async () => {
  loading.value = true;
  result.value = null;
  try {
    const response = await fetch('/api/design/pulse/design', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(design),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Design failed');
    }

    result.value = await response.json();
    emit('design-complete', result.value);
  } catch (error) {
    alert('Error running design: ' + error.message);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.step {
  transition: all 0.3s ease;
}
</style>
