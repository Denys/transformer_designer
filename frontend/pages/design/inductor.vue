<template>
  <div class="py-8">
    <div class="container">
      <h1 class="mb-6 fade-in">Inductor Design</h1>

      <div class="grid" style="grid-template-columns: 1fr 1.5fr; gap: 2rem;">
        <!-- Input Form -->
        <div class="card fade-in">
          <h3 style="margin-bottom: 1.5rem;">Design Requirements</h3>
          
          <form @submit.prevent="designInductor">
            <!-- Inductance Section -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                Inductance Specifications
              </h4>
              
              <div class="form-group">
                <label class="form-label">Inductance (μH)</label>
                <input 
                  v-model.number="requirements.inductance_uH" 
                  type="number" 
                  class="form-input"
                  min="0.1"
                  step="1"
                  required
                >
              </div>

              <div class="grid grid-2 gap-4">
                <div class="form-group">
                  <label class="form-label">DC Current (A)</label>
                  <input 
                    v-model.number="requirements.dc_current_A" 
                    type="number" 
                    class="form-input"
                    min="0"
                    step="0.1"
                    required
                  >
                </div>
                <div class="form-group">
                  <label class="form-label">Ripple Current (A p-p)</label>
                  <input 
                    v-model.number="requirements.ripple_current_A" 
                    type="number" 
                    class="form-input"
                    min="0.01"
                    step="0.1"
                    required
                  >
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Frequency (Hz)</label>
                <input 
                  v-model.number="requirements.frequency_Hz" 
                  type="number" 
                  class="form-input"
                  min="1000"
                  step="1000"
                  required
                >
              </div>
            </div>

            <!-- Operating Conditions -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                Operating Conditions
              </h4>
              
              <div class="grid grid-2 gap-4">
                <div class="form-group">
                  <label class="form-label">Ambient Temp (°C)</label>
                  <input 
                    v-model.number="requirements.ambient_temp_C" 
                    type="number" 
                    class="form-input"
                    min="-40"
                    max="85"
                  >
                </div>
                <div class="form-group">
                  <label class="form-label">Max Temp Rise (°C)</label>
                  <input 
                    v-model.number="requirements.max_temp_rise_C" 
                    type="number" 
                    class="form-input"
                    min="20"
                    max="100"
                  >
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Cooling</label>
                <select v-model="requirements.cooling" class="form-input form-select">
                  <option value="natural">Natural Convection</option>
                  <option value="forced">Forced Air</option>
                </select>
              </div>
            </div>

            <!-- Design Parameters -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                Design Parameters
              </h4>
              
              <div class="grid grid-2 gap-4">
                <div class="form-group">
                  <label class="form-label">Current Density (A/cm²)</label>
                  <input 
                    v-model.number="requirements.max_current_density_A_cm2" 
                    type="number" 
                    class="form-input"
                    min="100"
                    max="800"
                    step="50"
                  >
                </div>
                <div class="form-group">
                  <label class="form-label">Bmax Margin (%)</label>
                  <input 
                    v-model.number="requirements.Bmax_margin_percent" 
                    type="number" 
                    class="form-input"
                    min="10"
                    max="40"
                    step="5"
                  >
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg" style="width: 100%;" :disabled="loading">
              <span v-if="loading" class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></span>
              <span v-else>🧲 Design Inductor</span>
            </button>
          </form>

          <div v-if="error" class="mt-4" style="padding: 1rem; background: rgba(239,68,68,0.1); border-radius: var(--radius-md); border: 1px solid var(--color-error);">
            <strong style="color: var(--color-error);">Error:</strong>
            <span style="color: var(--color-text-secondary); margin-left: 0.5rem;">{{ error }}</span>
          </div>
        </div>

        <!-- Results Panel -->
        <div class="card fade-in">
          <h3 style="margin-bottom: 1.5rem;">Design Results</h3>

          <div v-if="!result && !loading" class="text-center py-12" style="color: var(--color-text-muted);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📋</div>
            <p>Enter requirements and click "Design Inductor" to generate a design</p>
          </div>

          <div v-if="loading" class="text-center py-12">
            <div class="spinner" style="margin: 0 auto;"></div>
            <p class="mt-4" style="color: var(--color-text-secondary);">Calculating optimal design...</p>
          </div>

          <div v-if="result" class="fade-in">
            <!-- Verification Status -->
            <div class="flex items-center gap-4 mb-6" style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
              <div class="flex items-center gap-2">
                <span class="verification-icon" :class="'verification-' + result.verification.electrical">✓</span>
                <span style="font-size: 0.85rem;">Saturation</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="verification-icon" :class="'verification-' + result.verification.mechanical">✓</span>
                <span style="font-size: 0.85rem;">Mechanical</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="verification-icon" :class="'verification-' + result.verification.thermal">✓</span>
                <span style="font-size: 0.85rem;">Thermal</span>
              </div>
              <div style="margin-left: auto;">
                <span 
                  class="badge" 
                  :class="result.design_viable ? 'badge-success' : 'badge-error'"
                >
                  {{ result.design_viable ? 'VIABLE' : 'NOT VIABLE' }}
                </span>
              </div>
            </div>

            <!-- Core Selection -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                Selected Core
              </h4>
              <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                <div class="flex justify-between items-center">
                  <div>
                    <strong style="font-size: 1.1rem;">{{ result.core.part_number }}</strong>
                    <span style="color: var(--color-text-muted); margin-left: 0.5rem;">{{ result.core.manufacturer }}</span>
                  </div>
                  <span class="badge badge-success">{{ result.core.geometry }}</span>
                </div>
                <div class="grid grid-4 gap-4 mt-4" style="font-size: 0.85rem;">
                  <div>
                    <div style="color: var(--color-text-muted);">Ae</div>
                    <div class="result-value" style="font-size: 1rem;">{{ result.core.Ae_cm2.toFixed(2) }}</div>
                    <span class="result-unit">cm²</span>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Ap</div>
                    <div class="result-value" style="font-size: 1rem;">{{ result.core.Ap_cm4.toFixed(2) }}</div>
                    <span class="result-unit">cm⁴</span>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Gap</div>
                    <div class="result-value" style="font-size: 1rem;">{{ result.air_gap_mm ? result.air_gap_mm.toFixed(2) : 'N/A' }}</div>
                    <span class="result-unit">mm</span>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Material</div>
                    <div style="font-weight: 600; color: var(--color-text-primary);">{{ result.core.material }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Flux Density -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                Flux Density
              </h4>
              <div class="grid grid-4 gap-4">
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                  <div style="color: var(--color-text-muted); font-size: 0.8rem;">Bdc</div>
                  <div class="result-value" style="font-size: 1rem;">{{ result.Bdc_T.toFixed(3) }}</div>
                  <span class="result-unit">T</span>
                </div>
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                  <div style="color: var(--color-text-muted); font-size: 0.8rem;">Bac</div>
                  <div class="result-value" style="font-size: 1rem;">{{ result.Bac_T.toFixed(3) }}</div>
                  <span class="result-unit">T</span>
                </div>
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                  <div style="color: var(--color-text-muted); font-size: 0.8rem;">Bpeak</div>
                  <div class="result-value" style="font-size: 1rem;">{{ result.Bpeak_T.toFixed(3) }}</div>
                  <span class="result-unit">T</span>
                </div>
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                  <div style="color: var(--color-text-muted); font-size: 0.8rem;">Margin</div>
                  <div class="result-value" style="font-size: 1rem;">{{ result.saturation_margin_percent.toFixed(1) }}</div>
                  <span class="result-unit">%</span>
                </div>
              </div>
            </div>

            <!-- Winding Design -->
            <div style="margin-bottom: 1.5rem;">
              <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                Winding Design
              </h4>
              <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                <div class="grid grid-4 gap-4" style="font-size: 0.85rem;">
                  <div>
                    <div style="color: var(--color-text-muted);">Turns</div>
                    <div style="font-weight: 600; font-size: 1.1rem; color: var(--color-text-primary);">{{ result.winding.turns }}</div>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Wire</div>
                    <div style="font-weight: 600; color: var(--color-text-primary);">AWG {{ result.winding.wire_awg }}</div>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Rdc</div>
                    <div style="font-weight: 600; color: var(--color-text-primary);">{{ result.winding.Rdc_mOhm.toFixed(2) }} mΩ</div>
                  </div>
                  <div>
                    <div style="color: var(--color-text-muted);">Fill</div>
                    <div style="font-weight: 600; color: var(--color-text-primary);">{{ (result.winding.window_utilization * 100).toFixed(1) }}%</div>
                  </div>
                </div>
              </div>
              <div class="mt-4 flex items-center gap-4">
                <span style="font-size: 0.85rem; color: var(--color-text-muted);">Calculated L:</span>
                <strong>{{ result.calculated_inductance_uH.toFixed(2) }} μH</strong>
                <span style="font-size: 0.85rem; color: var(--color-text-muted);">Tolerance:</span>
                <strong>{{ result.inductance_tolerance_percent.toFixed(1) }}%</strong>
              </div>
            </div>

            <!-- Loss & Thermal -->
            <div class="grid grid-2 gap-4">
              <div>
                <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">Losses</h4>
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                  <div style="font-size: 0.85rem; color: var(--color-text-secondary);">
                    <div class="flex justify-between"><span>Core:</span> <strong style="color: var(--color-text-primary);">{{ result.losses.core_loss_W.toFixed(3) }} W</strong></div>
                    <div class="flex justify-between"><span>Copper:</span> <strong style="color: var(--color-text-primary);">{{ result.losses.total_copper_loss_W.toFixed(3) }} W</strong></div>
                    <div class="flex justify-between" style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: 0.5rem; padding-top: 0.5rem;">
                      <span>Total:</span> <strong style="color: var(--color-accent-primary);">{{ result.losses.total_loss_W.toFixed(3) }} W</strong>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">Thermal</h4>
                <div style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                  <div style="font-size: 0.85rem; color: var(--color-text-secondary);">
                    <div class="flex justify-between"><span>Temp Rise:</span> <strong style="color: var(--color-text-primary);">{{ result.thermal.temperature_rise_C.toFixed(1) }} °C</strong></div>
                    <div class="flex justify-between"><span>Hotspot:</span> <strong style="color: var(--color-text-primary);">{{ result.thermal.hotspot_temp_C.toFixed(1) }} °C</strong></div>
                    <div class="flex justify-between"><span>Margin:</span> <strong style="color: var(--color-accent-primary);">{{ result.thermal.thermal_margin_C.toFixed(1) }} °C</strong></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Warnings -->
            <div v-if="result.verification.warnings.length > 0" class="mt-6" style="padding: 1rem; background: rgba(245,158,11,0.1); border: 1px solid var(--color-warning); border-radius: var(--radius-md);">
              <strong style="color: var(--color-warning);">⚠️ Warnings</strong>
              <ul style="margin-top: 0.5rem; margin-left: 1.5rem; font-size: 0.85rem; color: var(--color-text-secondary);">
                <li v-for="w in result.verification.warnings" :key="w">{{ w }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<any>(null)

const requirements = ref({
  inductance_uH: 100,
  dc_current_A: 5,
  ripple_current_A: 1,
  frequency_Hz: 100000,
  ambient_temp_C: 40,
  max_temp_rise_C: 50,
  cooling: 'natural',
  max_current_density_A_cm2: 400,
  Bmax_margin_percent: 20,
})

async function designInductor() {
  loading.value = true
  error.value = null
  result.value = null

  try {
    const response = await fetch('http://127.0.0.1:8000/api/design/inductor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requirements.value),
    })

    if (!response.ok) {
      const errData = await response.json()
      throw new Error(errData.detail || `HTTP ${response.status}`)
    }

    result.value = await response.json()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}
</script>
