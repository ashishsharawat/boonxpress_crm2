<template>
  <div class="h-full overflow-y-auto px-4 py-6">
    <div class="text-center mb-6">
      <h1 class="text-xl font-bold text-boon-text-primary font-heading">Welcome to {{ businessName }}!</h1>
      <p class="text-sm text-boon-text-secondary mt-1">Let's get your CRM set up in a few steps.</p>
    </div>

    <div class="space-y-3">
      <div v-for="(step, i) in steps" :key="i"
           class="flex items-center gap-3 bg-boon-surface rounded-xl px-4 py-3 cursor-pointer"
           :class="step.done ? 'opacity-60' : ''"
           @click="step.action">
        <div class="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
             :class="step.done ? 'bg-green-100 text-green-600' : 'bg-boon-primary-bg text-boon-primary'">
          <Check v-if="step.done" :size="14" />
          <span v-else class="text-xs font-bold">{{ i + 1 }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-boon-text-primary">{{ step.title }}</p>
          <p class="text-xs text-boon-text-secondary mt-0.5">{{ step.description }}</p>
        </div>
        <ChevronRight :size="16" class="text-gray-400 shrink-0" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Check, ChevronRight } from 'lucide-vue-next'
import { useVertical } from '@/composables/useVertical'

const { businessName } = useVertical()

const steps = ref([
  { title: 'Add your first client', description: 'Import or manually add a client', done: false, action: () => {} },
  { title: 'Connect WhatsApp', description: 'Link your WhatsApp Business account', done: false, action: () => {} },
  { title: 'Invite your team', description: 'Add up to 5 team members', done: false, action: () => {} },
  { title: 'Customize your CRM', description: 'Set up services, templates, and more', done: false, action: () => {} },
])
</script>
