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


# Map our internal template keys to the Meta conversation category that
# governs billing. Most are Utility (transactional); welcome promos can be
# Marketing depending on tenant choice. Conservative default: Utility.
TEMPLATE_CATEGORY = {
    "welcome": "Marketing",
    "appointment_reminder": "Utility",
    "re_engagement": "Marketing",
    "consent_request": "Utility",
}


@frappe.whitelist()
def send(template, recipient, params=None, vertical_type=None, waba_phone_id=None, country_code="IN"):
    """Render and dispatch a vertical-specific WhatsApp template.

    Wallet gating (v0.3.0): every paid send opens or reuses a 24h
    conversation log and deducts wallet credits before invoking
    frappe_whatsapp. If the wallet is empty (and no free quota or
    open conversation window) the send is rejected with
    `reason: insufficient_balance`.

    Args:
        template: One of VALID_TEMPLATES.
        recipient: E.164 phone number (e.g. "+919999900001").
        params: dict of template parameter values.
        vertical_type: Override; defaults to current site's vertical_type.
        waba_phone_id: Override; defaults to the tenant's default WABA.
        country_code: 2-letter; defaults to "IN".

    Returns:
        dict — `status` ∈ {sent, queued, error, insufficient_balance}.
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

    if not waba_phone_id:
        waba_phone_id = _resolve_default_waba_phone_id() or "unknown"

    # Wallet gate — reserve credits before hitting Meta.
    category = TEMPLATE_CATEGORY.get(template, "Utility")
    try:
        from boonxpress_crm.api import wallet as wallet_api
        reservation = wallet_api.check_and_reserve(
            category=category,
            customer_phone=recipient,
            waba_phone_id=waba_phone_id,
            country_code=country_code,
        )
    except Exception as e:
        frappe.log_error(f"Wallet reserve failed: {e}", "boonxpress_crm.whatsapp_send")
        return {"status": "error", "reason": "wallet_unavailable", "detail": str(e)}

    if not reservation.get("ok"):
        return {
            "status": "insufficient_balance" if reservation.get("reason") == "insufficient_balance" else "error",
            "reason": reservation.get("reason"),
            "detail": reservation,
        }

    # Now dispatch through frappe_whatsapp (or the fallback Communication
    # entry if frappe_whatsapp isn't installed yet).
    result = _dispatch_via_frappe_whatsapp(spec, recipient, params or {})

    # Commit or refund based on dispatch result.
    try:
        from boonxpress_crm.api import wallet as wallet_api
        if result.get("status") in ("sent", "queued"):
            meta_msg_id = (result.get("result") or {}).get("messages", [{}])[0].get("id") if isinstance(result.get("result"), dict) else None
            wallet_api.commit(reservation["reservation_id"], meta_message_id=meta_msg_id)
        else:
            wallet_api.refund(reservation["reservation_id"], reason=result.get("reason") or "Send failed")
    except Exception as e:
        frappe.log_error(f"Wallet commit/refund failed: {e}", "boonxpress_crm.whatsapp_send")

    # Surface billing info back to the caller for the UI.
    result["billing"] = {
        "charge_inr": reservation.get("charge_inr", 0),
        "is_free_quota_use": reservation.get("is_free_quota_use", False),
        "reused_window": reservation.get("reused_window", False),
        "reservation_id": reservation.get("reservation_id"),
    }
    return result


def _resolve_default_waba_phone_id():
    """Pull the default outgoing phone_id from frappe_whatsapp's WhatsApp Account, if installed."""
    try:
        if not frappe.db.exists("DocType", "WhatsApp Account"):
            return None
        return frappe.db.get_value(
            "WhatsApp Account",
            {"is_default_outgoing": 1},
            "phone_id",
        )
    except Exception:
        return None


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
