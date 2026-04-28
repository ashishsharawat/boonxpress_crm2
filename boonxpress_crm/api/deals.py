"""Deal stage transitions with optional transition notes.

Wraps `frappe.db.set_value` so the transition can be paired with an audit
Comment capturing the reason for the move. Validates against a whitelist
of valid stages drawn from all configured vertical pipelines.
"""

import frappe
from frappe import _


VALID_STATUSES = (
    # Frappe CRM defaults
    "Qualification",
    "Demo",
    "Proposal",
    "Negotiation",
    "Won",
    "Lost",
    # Auto vertical
    "Inspection",
    "Quote",
    # Used Car vertical
    "Test Drive",
    "Quote Sent",
    "Financing",
    # Med Spa vertical
    "Consultation",
    "Booked",
    # Course vertical
    "Enquiry",
    "Counselled",
    "Demo Class",
    "Payment Pending",
    "Enrolled",
)


@frappe.whitelist()
def transition_stage(deal_id, new_status, note=None):
    """Move a Deal to a new stage; optionally write a transition Comment."""
    if not deal_id:
        frappe.throw(_("Deal ID required"))
    if new_status not in VALID_STATUSES:
        frappe.throw(_("Invalid status: {0}").format(new_status))

    deal = frappe.get_doc("CRM Deal", deal_id)
    old_status = deal.status
    deal.status = new_status
    deal.save()

    if note:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": "CRM Deal",
            "reference_name": deal_id,
            "content": f"Stage: {old_status} → {new_status}. {note}",
        }).insert(ignore_permissions=True)

    return {
        "status": new_status,
        "deal_id": deal_id,
        "previous_status": old_status,
    }
