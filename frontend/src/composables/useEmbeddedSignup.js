import { ref, onMounted, onBeforeUnmount } from 'vue'
import { call } from '@/utils/api'

/**
 * Meta WhatsApp Embedded Signup client.
 *
 *   const { ready, connecting, connectedState, connect, disconnect, status } = useEmbeddedSignup()
 *   onMounted(() => status.refresh())
 *
 * The flow:
 * 1. Backend's get_signup_config() returns { meta_app_id, config_id, ready }.
 * 2. We lazy-load Facebook's JS SDK (https://connect.facebook.net/en_US/sdk.js).
 * 3. User clicks Connect → FB.login(callback, { config_id, response_type: 'code', extras: { feature: 'whatsapp_embedded_signup', sessionInfoVersion: 3 }}).
 * 4. We listen on `message` events for WA_EMBEDDED_SIGNUP postMessage from Meta's popup
 *    to pull `phone_number_id` + `waba_id` (FB.login alone doesn't return them).
 * 5. On both signals received, POST { code, phone_number_id, waba_id } to
 *    boonxpress_crm.api.embedded_signup.complete.
 *
 * If `meta_app_id` or `config_id` aren't configured server-side, `ready` is
 * false and the Connect button shows a "Platform not configured" hint.
 */

const FB_SDK_SRC = 'https://connect.facebook.net/en_US/sdk.js'

let _sdkLoadPromise = null

function loadFacebookSDK(appId, version = 'v20.0') {
  if (_sdkLoadPromise) return _sdkLoadPromise

  _sdkLoadPromise = new Promise((resolve, reject) => {
    if (window.FB) return resolve(window.FB)
    window.fbAsyncInit = function () {
      window.FB.init({ appId, cookie: true, xfbml: false, version })
      resolve(window.FB)
    }
    const script = document.createElement('script')
    script.src = FB_SDK_SRC
    script.async = true
    script.defer = true
    script.crossOrigin = 'anonymous'
    script.onerror = () => {
      _sdkLoadPromise = null
      reject(new Error('Failed to load Facebook SDK'))
    }
    document.head.appendChild(script)
  })
  return _sdkLoadPromise
}

export function useEmbeddedSignup() {
  const ready = ref(false)
  const connecting = ref(false)
  const error = ref('')
  const connectedState = ref({ connected: false })
  const config = ref({ meta_app_id: '', config_id: '', graph_api_version: 'v20.0', ready: false })

  let sessionData = { phone_number_id: '', waba_id: '' }

  function onPostMessage(event) {
    if (
      event.origin !== 'https://www.facebook.com'
      && event.origin !== 'https://web.facebook.com'
    ) {
      return
    }
    let parsed
    try {
      parsed = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
    } catch {
      return
    }
    if (parsed?.type !== 'WA_EMBEDDED_SIGNUP') return
    if (parsed?.event === 'FINISH' && parsed?.data) {
      sessionData = {
        phone_number_id: parsed.data.phone_number_id || '',
        waba_id: parsed.data.waba_id || '',
      }
    } else if (parsed?.event === 'CANCEL') {
      sessionData = { phone_number_id: '', waba_id: '' }
    }
  }

  onMounted(() => window.addEventListener('message', onPostMessage))
  onBeforeUnmount(() => window.removeEventListener('message', onPostMessage))

  async function init() {
    config.value = await call('boonxpress_crm.api.embedded_signup.get_signup_config')
    if (!config.value.ready) {
      ready.value = false
      return
    }
    try {
      await loadFacebookSDK(config.value.meta_app_id, config.value.graph_api_version)
      ready.value = true
    } catch (e) {
      error.value = e.message
      ready.value = false
    }
  }

  async function refreshStatus() {
    connectedState.value = await call('boonxpress_crm.api.embedded_signup.status')
  }

  async function connect() {
    if (!ready.value || connecting.value) return
    connecting.value = true
    error.value = ''
    sessionData = { phone_number_id: '', waba_id: '' }

    try {
      const code = await new Promise((resolve, reject) => {
        window.FB.login(
          (response) => {
            if (response.status === 'connected' && response.authResponse?.code) {
              resolve(response.authResponse.code)
            } else if (response.status === 'not_authorized') {
              reject(new Error('You declined the WhatsApp permission.'))
            } else {
              reject(new Error('Sign-in cancelled.'))
            }
          },
          {
            config_id: config.value.config_id,
            response_type: 'code',
            override_default_response_type: true,
            extras: {
              feature: 'whatsapp_embedded_signup',
              sessionInfoVersion: 3,
            },
          },
        )
      })

      // Wait briefly for the postMessage event to deliver phone_number_id + waba_id.
      // Meta sends these AFTER FB.login resolves; we poll up to 5 seconds.
      const start = Date.now()
      while (
        (!sessionData.phone_number_id || !sessionData.waba_id)
        && Date.now() - start < 5000
      ) {
        await new Promise((r) => setTimeout(r, 200))
      }
      if (!sessionData.phone_number_id || !sessionData.waba_id) {
        throw new Error("Sign-up didn't return a phone number — please retry.")
      }

      const result = await call('boonxpress_crm.api.embedded_signup.complete', {
        code,
        phone_number_id: sessionData.phone_number_id,
        waba_id: sessionData.waba_id,
      })

      if (!result.ok) {
        throw new Error(result.reason || 'Connection failed.')
      }

      await refreshStatus()
      return result
    } catch (e) {
      error.value = e.message || String(e)
      throw e
    } finally {
      connecting.value = false
    }
  }

  async function disconnect() {
    if (connecting.value) return
    connecting.value = true
    error.value = ''
    try {
      await call('boonxpress_crm.api.embedded_signup.disconnect')
      await refreshStatus()
    } catch (e) {
      error.value = e.message || String(e)
      throw e
    } finally {
      connecting.value = false
    }
  }

  return {
    ready,
    connecting,
    error,
    config,
    connectedState,
    init,
    refreshStatus,
    connect,
    disconnect,
  }
}
