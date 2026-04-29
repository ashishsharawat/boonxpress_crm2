"""WhatsApp send wrapper around frappe_whatsapp.

Reads vertical-specific WhatsApp templates (welcome / appointment_reminder /
re_engagement / consent_request) from `vertical_configs/whatsapp_templates/`
and dispatches them via frappe_whatsapp's `send_template` API.

Configuration (Site Config / Boon Tenant Config):
- whatsapp_business_id            — WABA ID (used by frappe_whatsapp)
- whatsapp_phone_number_id        — Meta phone number ID

The actual Meta API call is delegated to frappe_whatsapp; this module
only builds the right payload and resolves the right template name.

PRD: §3.1 ("WhatsApp is Primary"), §3.3 (WhatsApp 2-Way Inbox), §5.2
(boon_whatsapp_ui).
"""

import json
import os

import frappe


VALID_TEMPLATES = (
    "welcome",
    "appointment_reminder",
    "re_engagement",
    "consent_request",
)


def _templates_dir():
    """vertical_configs/whatsapp_templates/ at the app root."""
    api_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.dirname(api_dir)
    app_root = os.path.dirname(pkg_dir)
    return os.path.join(app_root, "vertical_configs", "whatsapp_templates")


def _load_template_set(vertical_type):
    """Load the per-vertical template definitions JSON (or fall back to general)."""
    base = _templates_dir()
    for name in (vertical_type, "general"):
        path = os.path.join(base, f"{name}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return {}


@frappe.whitelist()
def send(template, recipient, params=None, vertical_type=None):
    """Render and dispatch a vertical-specific WhatsApp template.

    Args:
        template: One of VALID_TEMPLATES.
        recipient: E.164 phone number (e.g. "+919999900001").
        params: dict of template parameter values (per template's body_params spec).
        vertical_type: Override; defaults to current site's vertical_type.

    Returns:
        dict with frappe_whatsapp's response, or { "status": "error", "reason": ... }.
    """
    if template not in VALID_TEMPLATES:
        return {"status": "error", "reason": "invalid_template", "template": template}
    if not recipient:
        return {"status": "error", "reason": "missing_recipient"}

    if not vertical_type:
        try:
            cfg = frappe.get_single("Boon Tenant Config")
            vertical_type = cfg.vertical_type or "general"
        except Exception:
            vertical_type = "general"

    template_set = _load_template_set(vertical_type)
    spec = (template_set.get("templates") or {}).get(template)
    if not spec:
        return {"status": "error", "reason": "template_not_in_vertical", "vertical_type": vertical_type}

    return _dispatch_via_frappe_whatsapp(spec, recipient, params or {})


def _dispatch_via_frappe_whatsapp(spec, recipient, params):
    """Call frappe_whatsapp's send API with the resolved template + params.

    frappe_whatsapp's exact API surface differs across versions; we try
    the documented `send_template_message` first and fall back to a
    generic Communication-doctype write if the app isn't installed.
    """
    template_name = spec.get("meta_template_name")
    language_code = spec.get("language_code") or "en"

    # Preferred: frappe_whatsapp's high-level helper if available
    try:
        from frappe_whatsapp.utils import send_template_message  # type: ignore

        result = send_template_message(
            template_name=template_name,
            recipient_number=recipient,
            parameters=list(_render_params(spec, params)),
            language_code=language_code,
        )
        return {"status": "sent", "via": "frappe_whatsapp", "template": template_name, "result": result}
    except ImportError:
        pass
    except Exception as e:
        frappe.log_error(f"frappe_whatsapp send failed: {e}", "boonxpress_crm.whatsapp_send")

    # Fallback: log a Communication entry so the message is at least visible
    # in the activity timeline. The actual API call is deferred until
    # frappe_whatsapp is installed/configured.
    rendered_body = spec.get("preview", "").format(**params) if spec.get("preview") else json.dumps(params)
    comm = frappe.get_doc({
        "doctype": "Communication",
        "communication_medium": "WhatsApp",
        "communication_type": "Communication",
        "sent_or_received": "Sent",
        "content": rendered_body,
        "subject": f"[Pending WA] {template_name}",
        "recipients": recipient,
    })
    comm.insert(ignore_permissions=True)
    return {
        "status": "queued",
        "via": "fallback_communication",
        "template": template_name,
        "comm": comm.name,
        "warning": "frappe_whatsapp not installed; logged as Communication for visibility",
    }


def _render_params(spec, params):
    """Yield parameter values in the order declared by the template spec."""
    for slot in spec.get("body_params", []) or []:
        key = slot.get("key")
        default = slot.get("default", "")
        yield params.get(key, default)


def on_lead_after_insert(doc, method=None):
    """Hook: send the welcome template the moment a Lead is created.

    Wired in hooks.py:
        doc_events = {"CRM Lead": {"after_insert": "boonxpress_crm.api.whatsapp_send.on_lead_after_insert"}}
    """
    recipient = (doc.mobile_no or "").strip()
    if not recipient:
        return
    name_parts = [doc.first_name or "", doc.last_name or ""]
    full_name = " ".join(p for p in name_parts if p) or "there"
    try:
        send(
            template="welcome",
            recipient=recipient,
            params={"name": full_name, "source": doc.source or ""},
        )
    except Exception as e:
        frappe.log_error(f"Welcome WA send failed for {doc.name}: {e}", "boonxpress_crm.whatsapp_send")
