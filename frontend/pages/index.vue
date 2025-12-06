<template>
  <div class="py-12">
    <div class="container">
      <!-- Hero Section -->
      <section class="text-center mb-6 fade-in">
        <h1 style="margin-bottom: 1rem;">
          Power Transformer Designer
        </h1>
        <p style="font-size: 1.25rem; max-width: 700px; margin: 0 auto;">
          Design transformers and inductors using McLyman's proven Area Product (Ap) 
          and Core Geometry (Kg) methodology
        </p>
      </section>

      <!-- Design Cards -->
      <section class="grid grid-2 mt-8 fade-in" style="max-width: 900px; margin: 3rem auto;">
        <!-- Transformer Card -->
        <NuxtLink to="/design/transformer" class="card" style="text-decoration: none;">
          <div class="text-center">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🔌</div>
            <h3 style="margin-bottom: 0.5rem;">Transformer Design</h3>
            <p style="font-size: 0.9rem;">
              Power transformers for SMPS, flyback, forward converters and more
            </p>
            <ul style="text-align: left; margin-top: 1rem; font-size: 0.85rem; color: var(--color-text-secondary);">
              <li>✓ Ap and Kg sizing methods</li>
              <li>✓ Core and material selection</li>
              <li>✓ Winding design with skin effect</li>
              <li>✓ Loss and thermal analysis</li>
            </ul>
            <div class="mt-4">
              <span class="btn btn-primary">Design Transformer →</span>
            </div>
          </div>
        </NuxtLink>

        <!-- Inductor Card -->
        <NuxtLink to="/design/inductor" class="card" style="text-decoration: none;">
          <div class="text-center">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🧲</div>
            <h3 style="margin-bottom: 0.5rem;">Inductor Design</h3>
            <p style="font-size: 0.9rem;">
              Energy storage inductors for PFC, buck, boost and filter applications
            </p>
            <ul style="text-align: left; margin-top: 1rem; font-size: 0.85rem; color: var(--color-text-secondary);">
              <li>✓ Energy storage method</li>
              <li>✓ Gap calculation</li>
              <li>✓ DC bias handling</li>
              <li>✓ Saturation verification</li>
            </ul>
            <div class="mt-4">
              <span class="btn btn-primary">Design Inductor →</span>
            </div>
          </div>
        </NuxtLink>
      </section>

      <!-- Features Section -->
      <section class="mt-8 fade-in">
        <h2 class="text-center mb-6">Key Features</h2>
        <div class="grid grid-4" style="max-width: 1100px; margin: 0 auto;">
          <div class="card text-center">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📐</div>
            <h4>McLyman Methodology</h4>
            <p style="font-size: 0.85rem;">Proven Ap/Kg sizing methods from the industry-standard handbook</p>
          </div>
          <div class="card text-center">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🗄️</div>
            <h4>Core Database</h4>
            <p style="font-size: 0.85rem;">Ferrite and silicon steel cores from major manufacturers</p>
          </div>
          <div class="card text-center">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔬</div>
            <h4>Loss Analysis</h4>
            <p style="font-size: 0.85rem;">Steinmetz core loss and AC copper loss with skin effect</p>
          </div>
          <div class="card text-center">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌡️</div>
            <h4>Thermal Verification</h4>
            <p style="font-size: 0.85rem;">Temperature rise prediction and cooling recommendations</p>
          </div>
        </div>
      </section>

      <!-- API Status -->
      <section class="mt-8 text-center fade-in">
        <div class="card" style="max-width: 400px; margin: 0 auto;">
          <h4 style="margin-bottom: 0.5rem;">API Status</h4>
          <div v-if="loading" class="flex justify-center mt-4">
            <div class="spinner"></div>
          </div>
          <div v-else-if="apiStatus" class="flex items-center justify-center gap-2 mt-4">
            <span class="badge badge-success">● Online</span>
            <span style="font-size: 0.85rem; color: var(--color-text-muted);">v{{ apiStatus.version }}</span>
          </div>
          <div v-else class="flex items-center justify-center gap-2 mt-4">
            <span class="badge badge-error">● Offline</span>
            <span style="font-size: 0.85rem; color: var(--color-text-muted);">Backend not running</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const loading = ref(true)
const apiStatus = ref<{ status: string; version: string } | null>(null)

onMounted(async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/health')
    if (response.ok) {
      apiStatus.value = await response.json()
    }
  } catch (e) {
    console.error('API health check failed:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
section ul {
  list-style: none;
}

section ul li {
  padding: 0.25rem 0;
}
</style>
