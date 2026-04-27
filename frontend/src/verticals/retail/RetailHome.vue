<template>
  <div class="h-full flex flex-col items-center justify-center px-6 text-center">
    <ShoppingBag :size="48" class="text-boon-primary-light mb-3" />
    <h2 class="text-lg font-semibold text-boon-text-primary font-heading">Retail Dashboard</h2>
    <p class="text-sm text-boon-text-secondary mt-1">Order tracking and catalogue sharing coming soon.</p>
  </div>
</template>

<script setup>
import { ShoppingBag } from 'lucide-vue-next'
</script>
