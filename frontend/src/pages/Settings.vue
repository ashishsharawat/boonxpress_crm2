<template>
  <div class="h-full overflow-y-auto px-4 py-4 space-y-4">
    <!-- Business Info -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Business</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Name</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ businessName }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Type</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ displayName }}</span>
        </div>
      </div>
    </div>

    <!-- Account -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">Account</h3>
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">User</span>
          <span class="text-sm text-boon-text-primary font-medium">{{ userEmail }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-sm text-boon-text-secondary">Plan</span>
          <span class="text-sm text-boon-text-primary font-medium">₹999/mo</span>
        </div>
      </div>
    </div>

    <!-- WhatsApp Status -->
    <div class="bg-boon-surface rounded-2xl p-4">
      <h3 class="text-xs font-semibold text-boon-text-secondary uppercase tracking-wider mb-3">WhatsApp</h3>
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-yellow-500" />
        <span class="text-sm text-boon-text-secondary">Not connected</span>
      </div>
      <p class="text-xs text-boon-text-secondary mt-2">Connect your WhatsApp Business account to send and receive messages from the CRM.</p>
    </div>

    <!-- App Version -->
    <div class="text-center py-2">
      <p class="text-[10px] text-gray-400">BoonCRM v0.1.0</p>
    </div>
  </div>
</template>

<script setup>
import { useVertical } from '@/composables/useVertical'
import { useSessionStore } from '@/stores/session'

const { businessName, displayName } = useVertical()
const session = useSessionStore()
const userEmail = session.userEmail
</script>
