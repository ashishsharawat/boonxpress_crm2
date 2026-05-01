"""WhatsApp Conversation Log — one row per (waba_phone_id, customer_phone,
category, 24h-window). Drives conversation-based billing.
"""

from frappe.model.document import Document


class WhatsAppConversationLog(Document):
    pass
