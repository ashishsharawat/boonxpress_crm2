<template>
  <div class="h-full flex flex-col items-center justify-center px-6 text-center">
    <div class="w-16 h-16 rounded-full bg-boon-primary-bg flex items-center justify-center mb-4">
      <AlertCircle :size="28" class="text-boon-primary" />
    </div>
    <h2 class="text-lg font-semibold text-boon-text-primary font-heading">Page not found</h2>
    <p class="text-sm text-boon-text-secondary mt-1">The page you're looking for doesn't exist.</p>
    <router-link to="/" class="mt-4 px-4 py-2 bg-boon-primary text-white text-sm rounded-xl font-medium cursor-pointer">
      Go Home
    </router-link>
  </div>
</template>

<script setup>
import { AlertCircle } from 'lucide-vue-next'
</script>
