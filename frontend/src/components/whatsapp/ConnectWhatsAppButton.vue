<template>
  <div class="bg-boon-surface rounded-xl p-4 space-y-3">
    <div class="flex items-start gap-3">
      <div class="bg-emerald-100 w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0">
        <MessageCircle :size="18" class="text-emerald-700" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-semibold text-boon-text-primary">WhatsApp Business</h3>
          <span
            v-if="connectedState.connected"
            class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800"
          >CONNECTED</span>
          <span
            v-else
            class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600"
          >NOT CONNECTED</span>
        </div>
        <p v-if="connectedState.connected" class="text-xs text-boon-text-secondary mt-1 truncate">
          {{ connectedState.account_name }} · phone {{ connectedState.phone_id }}
        </p>
        <p v-else class="text-xs text-boon-text-secondary mt-1">
          Connect your WhatsApp Business Account to send + receive messages from this CRM.
        </p>
      </div>
    </div>

    <p v-if="error" class="text-xs text-red-600">{{ error }}</p>

    <p v-if="!ready && !platformConfigured" class="text-xs text-amber-600">
      WhatsApp connection isn't configured on this platform yet. Contact your operator.
    </p>

    <div class="flex gap-2">
      <button
        v-if="!connectedState.connected"
        @click="onConnect"
        :disabled="!ready || connecting"
        class="flex-1 py-2 rounded-lg bg-boon-primary text-white text-sm font-semibold disabled:opacity-50"
      >
        {{ connecting ? 'Connecting…' : 'Connect WhatsApp' }}
      </button>
      <button
        v-else
        @click="onDisconnect"
        :disabled="connecting"
        class="flex-1 py-2 rounded-lg bg-gray-100 text-boon-text-primary text-sm font-semibold disabled:opacity-50"
      >
        {{ connecting ? 'Working…' : 'Disconnect' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { MessageCircle } from 'lucide-vue-next'
import { useEmbeddedSignup } from '@/composables/useEmbeddedSignup'

const {
  ready,
  connecting,
  error,
  config,
  connectedState,
  init,
  refreshStatus,
  connect,
  disconnect,
} = useEmbeddedSignup()

const platformConfigured = computed(() => config.value?.ready)

onMounted(async () => {
  await Promise.all([init(), refreshStatus()])
})

async function onConnect() {
  try {
    await connect()
  } catch {
    // Error already surfaced via the `error` ref
  }
}

async function onDisconnect() {
  try {
    await disconnect()
  } catch {
    // Surfaced via `error` ref
  }
}
</script>
