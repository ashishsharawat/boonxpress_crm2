export function useWhatsApp() {
  /**
   * Open WhatsApp chat with a phone number.
   * Uses wa.me deeplink which works on all platforms.
   */
  function openChat(phoneNumber, message = '') {
    if (!phoneNumber) return

    // Normalize phone number — remove spaces, dashes, ensure country code
    let phone = phoneNumber.replace(/[\s\-()]/g, '')
    if (phone.startsWith('0')) {
      phone = '91' + phone.slice(1) // Default to India country code
    }
    if (!phone.startsWith('+') && !phone.startsWith('91')) {
      phone = '91' + phone
    }
    phone = phone.replace('+', '')

    const url = message
      ? `https://wa.me/${phone}?text=${encodeURIComponent(message)}`
      : `https://wa.me/${phone}`

    window.open(url, '_blank')
  }

  /**
   * Send a WhatsApp message via frappe_whatsapp API.
   */
  async function sendMessage(to, template, params = {}) {
    try {
      const response = await fetch('/api/method/frappe_whatsapp.api.send_template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': window.csrf_token || '',
        },
        body: JSON.stringify({ to, template, params }),
      })
      return response.ok
    } catch (err) {
      console.error('WhatsApp send failed:', err)
      return false
    }
  }

  return { openChat, sendMessage }
}
