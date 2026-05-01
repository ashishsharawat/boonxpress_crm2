"""WhatsApp Credit Transaction — append-only audit log of wallet movements.

Created exclusively by `boonxpress_crm.api.wallet`. Marked read-only via
permissions so a tenant admin can audit but never edit history.
"""

from frappe.model.document import Document


class WhatsAppCreditTransaction(Document):
    pass
