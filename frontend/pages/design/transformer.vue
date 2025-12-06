<template>
    <div class="py-8">
        <div class="container">
            <h1 class="mb-6 fade-in">Transformer Design</h1>

            <div class="grid" style="grid-template-columns: 1fr 1.5fr; gap: 2rem;">
                <!-- Input Form -->
                <div class="card fade-in">
                    <h3 style="margin-bottom: 1.5rem;">Design Requirements</h3>

                    <form @submit.prevent="designTransformer">
                        <!-- Power Section -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                                Power Specifications
                            </h4>

                            <div class="form-group">
                                <label class="form-label">Output Power (W)</label>
                                <input v-model.number="requirements.output_power_W" type="number" class="form-input"
                                    min="1" step="1" required>
                            </div>

                            <div class="grid grid-2 gap-4">
                                <div class="form-group">
                                    <label class="form-label">Primary Voltage (V)</label>
                                    <input v-model.number="requirements.primary_voltage_V" type="number"
                                        class="form-input" min="1" step="0.1" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Secondary Voltage (V)</label>
                                    <input v-model.number="requirements.secondary_voltage_V" type="number"
                                        class="form-input" min="1" step="0.1" required>
                                </div>
                            </div>

                            <div class="form-group">
                                <label class="form-label">Frequency (Hz)</label>
                                <input v-model.number="requirements.frequency_Hz" type="number" class="form-input"
                                    min="50" step="1000" required>
                            </div>
                        </div>

                        <!-- Operating Conditions -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                                Operating Conditions
                            </h4>

                            <div class="grid grid-2 gap-4">
                                <div class="form-group">
                                    <label class="form-label">Efficiency Target (%)</label>
                                    <input v-model.number="requirements.efficiency_percent" type="number"
                                        class="form-input" min="50" max="99.9" step="0.5">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Regulation (%)</label>
                                    <input v-model.number="requirements.regulation_percent" type="number"
                                        class="form-input" min="0.5" max="20" step="0.5">
                                </div>
                            </div>

                            <div class="grid grid-2 gap-4">
                                <div class="form-group">
                                    <label class="form-label">Ambient Temp (°C)</label>
                                    <input v-model.number="requirements.ambient_temp_C" type="number" class="form-input"
                                        min="-40" max="85">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Max Temp Rise (°C)</label>
                                    <input v-model.number="requirements.max_temp_rise_C" type="number"
                                        class="form-input" min="20" max="100">
                                </div>
                            </div>

                            <div class="form-group">
                                <label class="form-label">Cooling</label>
                                <select v-model="requirements.cooling" class="form-input form-select">
                                    <option value="natural">Natural Convection</option>
                                    <option value="forced">Forced Air</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="form-label">
                                    Design Method
                                    <span class="help-icon" title="Select core sizing methodology">ⓘ</span>
                                </label>
                                <select v-model="requirements.design_method" class="form-input form-select">
                                    <option value="auto">Auto (Recommended)</option>
                                    <option value="ap_mclyman">McLyman Ap — General purpose</option>
                                    <option value="kg_mclyman">McLyman Kg — Low frequency, regulation</option>
                                    <option value="kgfe_erickson">Erickson Kgfe — Loss optimized (HF)</option>
                                </select>
                                <div class="form-hint">
                                    <strong>Auto:</strong> Best method for your frequency/power |
                                    <strong>Erickson:</strong> Minimizes total loss for SMPS
                                </div>
                            </div>
                        </div>

                        <!-- Design Parameters -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 1rem;">
                                Design Parameters
                            </h4>

                            <div class="form-group">
                                <label class="form-label">
                                    Waveform
                                    <span class="help-icon" title="Affects form factor Kf in Faraday's law">ⓘ</span>
                                </label>
                                <select v-model="requirements.waveform" class="form-input form-select">
                                    <option value="sinusoidal">Sinusoidal (Kf = 4.44) — Line frequency, resonant
                                    </option>
                                    <option value="square">Square Wave (Kf = 4.0) — SMPS, full-bridge, push-pull
                                    </option>
                                    <option value="triangular">Triangular (Kf = 4.0) — Flyback, forward converters
                                    </option>
                                </select>
                                <div class="form-hint">
                                    <strong>Sinusoidal:</strong> AC mains, resonant converters |
                                    <strong>Square:</strong> Full-bridge, half-bridge, push-pull |
                                    <strong>Triangular:</strong> Flyback, forward (DCM)
                                </div>
                            </div>

                            <div class="grid grid-2 gap-4">
                                <div class="form-group">
                                    <label class="form-label">
                                        Current Density J (A/cm²)
                                        <span class="help-icon"
                                            title="Higher J = smaller wire, more losses, hotter">ⓘ</span>
                                    </label>
                                    <input v-model.number="requirements.max_current_density_A_cm2" type="number"
                                        class="form-input" min="100" max="800" step="50">
                                    <div class="form-hint">
                                        <strong>200-300:</strong> Conservative, low losses |
                                        <strong>400-500:</strong> Typical SMPS |
                                        <strong>600+:</strong> Compact, forced cooling required
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">
                                        Window Fill Ku
                                        <span class="help-icon" title="Fraction of window area used by copper">ⓘ</span>
                                    </label>
                                    <input v-model.number="requirements.window_utilization_Ku" type="number"
                                        class="form-input" min="0.15" max="0.55" step="0.05">
                                    <div class="form-hint">
                                        <strong>0.25-0.30:</strong> Multiple windings, safety margins |
                                        <strong>0.35-0.40:</strong> Standard bobbin wound |
                                        <strong>0.45-0.55:</strong> Tight, layer-wound
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary btn-lg" style="width: 100%;" :disabled="loading">
                            <span v-if="loading" class="spinner"
                                style="width: 20px; height: 20px; border-width: 2px;"></span>
                            <span v-else>🔧 Design Transformer</span>
                        </button>
                    </form>

                    <div v-if="error" class="mt-4"
                        style="padding: 1rem; background: rgba(239,68,68,0.1); border-radius: var(--radius-md); border: 1px solid var(--color-error);">
                        <strong style="color: var(--color-error);">Error:</strong>
                        <span style="color: var(--color-text-secondary); margin-left: 0.5rem;">{{ error }}</span>
                    </div>
                </div>

                <!-- Results Panel -->
                <div class="card fade-in">
                    <h3 style="margin-bottom: 1.5rem;">Design Results</h3>

                    <div v-if="!result && !suggestions && !loading" class="text-center py-12"
                        style="color: var(--color-text-muted);">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">📋</div>
                        <p>Enter requirements and click "Design Transformer" to generate a design</p>
                    </div>

                    <div v-if="loading" class="text-center py-12">
                        <div class="spinner" style="margin: 0 auto;"></div>
                        <p class="mt-4" style="color: var(--color-text-secondary);">Calculating optimal design...</p>
                    </div>

                    <!-- SUGGESTIONS PANEL (No core found) -->
                    <div v-if="suggestions" class="fade-in">
                        <div class="mb-6"
                            style="padding: 1rem; background: rgba(245,158,11,0.15); border: 1px solid var(--color-warning); border-radius: var(--radius-md);">
                            <div class="flex items-center gap-2">
                                <span style="font-size: 1.5rem;">⚠️</span>
                                <strong style="color: var(--color-warning);">{{ suggestions.message }}</strong>
                            </div>
                            <div style="margin-top: 0.75rem; font-size: 0.9rem; color: var(--color-text-secondary);">
                                Required: <strong>{{ suggestions.required_Ap_cm4.toFixed(1) }} cm⁴</strong> |
                                Available: <strong>{{ suggestions.available_max_Ap_cm4.toFixed(1) }} cm⁴</strong>
                            </div>
                        </div>

                        <!-- Parameter Suggestions -->
                        <div v-if="suggestions.suggestions.length > 0" style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                💡 Try These Parameter Changes
                            </h4>
                            <div class="flex flex-col gap-2">
                                <div v-for="s in suggestions.suggestions" :key="s.parameter"
                                    style="padding: 0.75rem 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s;"
                                    :style="s.feasible ? 'border: 1px solid rgba(16,185,129,0.3)' : 'border: 1px solid rgba(245,158,11,0.3)'"
                                    @click="applySuggestionAndRetry(s)">
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <strong style="color: var(--color-text-primary);">{{
                                                formatParamName(s.parameter) }}</strong>
                                            <span style="color: var(--color-text-muted); margin-left: 0.5rem;">
                                                {{ s.current_value }} {{ s.unit }} →
                                                <span
                                                    :style="s.feasible ? 'color: var(--color-success)' : 'color: var(--color-warning)'">
                                                    {{ s.suggested_value }} {{ s.unit }}
                                                </span>
                                            </span>
                                        </div>
                                        <span class="badge" :class="s.feasible ? 'badge-success' : 'badge-warning'">
                                            {{ s.feasible ? 'Apply' : 'Risky' }}
                                        </span>
                                    </div>
                                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--color-text-muted);">
                                        {{ s.impact }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Closest Available Cores -->
                        <div v-if="suggestions.closest_cores.length > 0" style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                📦 Largest Available Cores
                            </h4>
                            <div class="grid gap-2">
                                <div v-for="c in suggestions.closest_cores" :key="c.part_number"
                                    style="padding: 0.75rem 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <strong>{{ c.part_number }}</strong>
                                            <span style="color: var(--color-text-muted); margin-left: 0.5rem;">{{
                                                c.manufacturer }}</span>
                                        </div>
                                        <span class="badge badge-success">{{ c.geometry }}</span>
                                    </div>
                                    <div
                                        style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--color-text-secondary);">
                                        Ap: <strong>{{ c.Ap_cm4.toFixed(2) }} cm⁴</strong> |
                                        Max Power: <strong>{{ c.max_power_W.toFixed(0) }} W</strong>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Alternative Approaches -->
                        <div v-if="suggestions.alternative_approaches.length > 0">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                🔧 Alternative Approaches
                            </h4>
                            <ul style="margin-left: 1.5rem; font-size: 0.9rem; color: var(--color-text-secondary);">
                                <li v-for="a in suggestions.alternative_approaches" :key="a"
                                    style="padding: 0.25rem 0;">
                                    {{ a }}
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!-- SUCCESS RESULT -->
                    <div v-if="result" class="fade-in">
                        <!-- Verification Status -->
                        <div class="flex items-center gap-4 mb-6"
                            style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                            <div class="flex items-center gap-2">
                                <span class="verification-icon"
                                    :class="'verification-' + result.verification.electrical">✓</span>
                                <span style="font-size: 0.85rem;">Electrical</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="verification-icon"
                                    :class="'verification-' + result.verification.mechanical">✓</span>
                                <span style="font-size: 0.85rem;">Mechanical</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="verification-icon"
                                    :class="'verification-' + result.verification.thermal">✓</span>
                                <span style="font-size: 0.85rem;">Thermal</span>
                            </div>
                            <div style="margin-left: auto;">
                                <span class="badge" :class="result.design_viable ? 'badge-success' : 'badge-error'">
                                    {{ result.design_viable ? 'VIABLE' : 'NOT VIABLE' }}
                                </span>
                            </div>
                        </div>

                        <!-- Core Selection -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                Selected Core
                            </h4>
                            <div
                                style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <strong style="font-size: 1.1rem;">{{ result.core.part_number }}</strong>
                                        <span style="color: var(--color-text-muted); margin-left: 0.5rem;">{{
                                            result.core.manufacturer }}</span>
                                    </div>
                                    <div class="flex gap-2 items-center">
                                        <!-- Source Badge -->
                                        <span class="badge"
                                            :class="result.core.source === 'openmagnetics' ? 'badge-openmagnetics' : 'badge-local'"
                                            :title="result.core.source === 'openmagnetics' ? 'Found via OpenMagnetics (10,000+ cores)' : 'From local database'">
                                            {{ result.core.source === 'openmagnetics' ? '🌐 OpenMagnetics' : '📦 Local'
                                            }}
                                        </span>
                                        <span class="badge badge-success">{{ result.core.geometry }}</span>
                                    </div>
                                </div>

                                <!-- Datasheet Link (if available) -->
                                <div v-if="result.core.datasheet_url" style="margin-top: 0.75rem;">
                                    <a :href="result.core.datasheet_url" target="_blank" rel="noopener noreferrer"
                                        class="datasheet-link">
                                        📄 View Datasheet →
                                    </a>
                                </div>

                                <div class="grid grid-4 gap-4 mt-4" style="font-size: 0.85rem;">
                                    <div>
                                        <div style="color: var(--color-text-muted);">Ae</div>
                                        <div class="result-value" style="font-size: 1rem;">{{
                                            result.core.Ae_cm2.toFixed(2) }}</div>
                                        <span class="result-unit">cm²</span>
                                    </div>
                                    <div>
                                        <div style="color: var(--color-text-muted);">Ap</div>
                                        <div class="result-value" style="font-size: 1rem;">{{
                                            result.core.Ap_cm4.toFixed(2) }}</div>
                                        <span class="result-unit">cm⁴</span>
                                    </div>
                                    <div>
                                        <div style="color: var(--color-text-muted);">Bmax</div>
                                        <div class="result-value" style="font-size: 1rem;">{{
                                            result.core.Bmax_T.toFixed(2) }}</div>
                                        <span class="result-unit">T</span>
                                    </div>
                                    <div>
                                        <div style="color: var(--color-text-muted);">Material</div>
                                        <div style="font-weight: 600; color: var(--color-text-primary);">{{
                                            result.core.material }}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Alternative Cores -->
                            <div v-if="result.alternative_cores && result.alternative_cores.length > 0"
                                style="margin-top: 1rem; padding: 0.75rem; background: var(--color-bg-secondary); border-radius: var(--radius-md);">
                                <div style="font-size: 0.8rem; color: var(--color-text-muted); margin-bottom: 0.5rem;">
                                    💡 Click to use an alternative core:
                                </div>
                                <div class="flex gap-2 flex-wrap">
                                    <button v-for="alt in result.alternative_cores" :key="alt.part_number"
                                        class="alt-core-chip alt-core-clickable"
                                        :title="`Click to redesign with ${alt.part_number} | ${alt.manufacturer} | Ap: ${alt.Ap_cm4?.toFixed(2)} cm⁴`"
                                        @click="selectAlternativeCore(alt)">
                                        {{ alt.part_number }}
                                        <span class="alt-core-source">{{ alt.source === 'openmagnetics' ? '🌐' : '📦'
                                        }}</span>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Winding Design -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                Winding Design
                            </h4>
                            <div class="grid grid-2 gap-4">
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Primary</div>
                                    <div style="font-size: 0.85rem; color: var(--color-text-secondary);">
                                        <div>Turns: <strong style="color: var(--color-text-primary);">{{
                                            result.winding.primary_turns }}</strong></div>
                                        <div>Wire: <strong style="color: var(--color-text-primary);">AWG {{
                                            result.winding.primary_wire_awg }}</strong></div>
                                        <div>Rdc: <strong style="color: var(--color-text-primary);">{{
                                            result.winding.primary_Rdc_mOhm.toFixed(2) }} mΩ</strong></div>
                                    </div>
                                </div>
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md);">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Secondary</div>
                                    <div style="font-size: 0.85rem; color: var(--color-text-secondary);">
                                        <div>Turns: <strong style="color: var(--color-text-primary);">{{
                                            result.winding.secondary_turns }}</strong></div>
                                        <div>Wire: <strong style="color: var(--color-text-primary);">AWG {{
                                            result.winding.secondary_wire_awg }}</strong></div>
                                        <div>Rdc: <strong style="color: var(--color-text-primary);">{{
                                            result.winding.secondary_Rdc_mOhm.toFixed(2) }} mΩ</strong></div>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-4 flex items-center gap-2">
                                <span style="font-size: 0.85rem; color: var(--color-text-muted);">Turns ratio:</span>
                                <strong>{{ result.turns_ratio.toFixed(3) }}</strong>
                                <span
                                    style="margin-left: 1rem; font-size: 0.85rem; color: var(--color-text-muted);">Window
                                    fill:</span>
                                <strong>{{ (result.winding.total_Ku * 100).toFixed(1) }}%</strong>
                            </div>
                        </div>

                        <!-- Loss Analysis -->
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                Loss Analysis
                            </h4>
                            <div class="grid grid-3 gap-4">
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Core Loss</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.losses.core_loss_W.toFixed(2) }}</div>
                                    <span class="result-unit">W</span>
                                </div>
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Copper Loss</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.losses.total_copper_loss_W.toFixed(2) }}</div>
                                    <span class="result-unit">W</span>
                                </div>
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Efficiency</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.losses.efficiency_percent.toFixed(1) }}</div>
                                    <span class="result-unit">%</span>
                                </div>
                            </div>
                        </div>

                        <!-- Thermal Analysis -->
                        <div>
                            <h4 style="font-size: 0.9rem; color: var(--color-accent-primary); margin-bottom: 0.75rem;">
                                Thermal Analysis
                            </h4>
                            <div class="grid grid-3 gap-4">
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Temp Rise</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.thermal.temperature_rise_C.toFixed(1) }}</div>
                                    <span class="result-unit">°C</span>
                                </div>
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Hotspot</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.thermal.hotspot_temp_C.toFixed(1) }}</div>
                                    <span class="result-unit">°C</span>
                                </div>
                                <div
                                    style="padding: 1rem; background: var(--color-bg-tertiary); border-radius: var(--radius-md); text-align: center;">
                                    <div style="color: var(--color-text-muted); font-size: 0.8rem;">Margin</div>
                                    <div class="result-value" style="font-size: 1.25rem;">{{
                                        result.thermal.thermal_margin_C.toFixed(1) }}</div>
                                    <span class="result-unit">°C</span>
                                </div>
                            </div>
                        </div>

                        <!-- Warnings/Recommendations -->
                        <div v-if="result.verification.warnings.length > 0 || result.verification.recommendations.length > 0"
                            class="mt-6">
                            <div v-if="result.verification.warnings.length > 0"
                                style="padding: 1rem; background: rgba(245,158,11,0.1); border: 1px solid var(--color-warning); border-radius: var(--radius-md); margin-bottom: 1rem;">
                                <strong style="color: var(--color-warning);">⚠️ Warnings</strong>
                                <ul
                                    style="margin-top: 0.5rem; margin-left: 1.5rem; font-size: 0.85rem; color: var(--color-text-secondary);">
                                    <li v-for="w in result.verification.warnings" :key="w">{{ w }}</li>
                                </ul>
                            </div>
                            <div v-if="result.verification.recommendations.length > 0"
                                style="padding: 1rem; background: rgba(59,130,246,0.1); border: 1px solid var(--color-info); border-radius: var(--radius-md);">
                                <strong style="color: var(--color-info);">💡 Recommendations</strong>
                                <ul
                                    style="margin-top: 0.5rem; margin-left: 1.5rem; font-size: 0.85rem; color: var(--color-text-secondary);">
                                    <li v-for="r in result.verification.recommendations" :key="r">{{ r }}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useTransformerDesign, type DesignSuggestion, type AlternativeCore } from '~/composables/useTransformerDesign'

const { requirements, loading, error, result, suggestions, designTransformer, applySuggestion } = useTransformerDesign()

function formatParamName(param: string): string {
    const names: Record<string, string> = {
        output_power_W: 'Output Power',
        frequency_Hz: 'Frequency',
        max_current_density_A_cm2: 'Current Density',
        window_utilization_Ku: 'Window Fill (Ku)',
    }
    return names[param] || param.replace(/_/g, ' ')
}

async function applySuggestionAndRetry(suggestion: DesignSuggestion) {
    applySuggestion(suggestion)
    await designTransformer()
}

async function selectAlternativeCore(alt: AlternativeCore) {
    // Extract geometry from part number (e.g., "ETD54" -> "ETD", "PQ40/40" -> "PQ")
    const geometry = alt.geometry || alt.part_number.match(/^[A-Z]+/i)?.[0] || ''
    if (geometry) {
        requirements.value.preferred_core_geometry = geometry
    }
    // Re-run design - the backend will try to select this core
    await designTransformer()
}
</script>
