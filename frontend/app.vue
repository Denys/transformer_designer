<template>
  <div>
    <header class="header">
      <div class="container header-content">
        <div class="logo">
          <div class="logo-icon">⚡</div>
          <span class="logo-text">Transformer Designer</span>
        </div>
        <nav class="flex gap-4">
          <NuxtLink to="/" class="btn btn-secondary">Home</NuxtLink>
          <NuxtLink to="/design/transformer" class="btn btn-secondary">Transformer</NuxtLink>
          <NuxtLink to="/design/inductor" class="btn btn-secondary">Inductor</NuxtLink>
        </nav>
      </div>
    </header>
    
    <main>
      <NuxtPage />
    </main>
    
    <footer class="py-8" style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: auto;">
      <div class="container text-center">
        <p style="font-size: 0.875rem;">
          Power Transformer Designer — McLyman's Ap/Kg Methodology
        </p>
        <p style="font-size: 0.75rem; margin-top: 0.5rem; color: var(--color-text-muted);">
          Developed by DK and Lumina from Electronic Systems Architects (ESA)
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
// App-level setup
</script>

<style>
/* Global app styles */
#__nuxt {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
</style>
