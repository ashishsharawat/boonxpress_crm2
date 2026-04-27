<template>
  <div class="h-full flex flex-col items-center justify-center px-6 text-center">
    <Stethoscope :size="48" class="text-boon-primary-light mb-3" />
    <h2 class="text-lg font-semibold text-boon-text-primary font-heading">Clinic Dashboard</h2>
    <p class="text-sm text-boon-text-secondary mt-1">Patient timeline and consultation pipeline coming soon.</p>
  </div>
</template>

<script setup>
import { Stethoscope } from 'lucide-vue-next'
</script>
