"""Meta Lead Ads webhook receiver.

When a user submits a Lead Ads form on Facebook or Instagram, Meta POSTs
to this endpoint. We verify the signature (HMAC-SHA256 with the app
secret), pull the lead details via Graph API, and create a CRM Lead with
correct field mapping per vertical.

Configuration (Site Config / Boon Tenant Config):
- meta_app_secret             — for HMAC signature verification
- meta_page_access_token      — for Graph API lead fetch
- meta_lead_field_map         — JSON map of Meta lead form field IDs → CRM Lead fields
                                (defaults shipped per vertical, can be overridden)

The webhook URL whitelisted in Meta's Lead Ads form settings is:
    https://<tenant>.booncrm.in/api/method/boonxpress_crm.api.meta_leads.webhook

PRD: §3.3 (FB lead capture), §5.2 (boon_meta_leads).
"""

import hashlib
import hmac
import json

import frappe
from frappe import _


# Default mapping of Meta Lead form fields → CRM Lead fields.
# Tenant-specific overrides go in Boon Tenant Config.meta_lead_field_map.
DEFAULT_FIELD_MAP = {
    "full_name": "lead_name",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone_number": "mobile_no",
    "phone": "mobile_no",
}


@frappe.whitelist(allow_guest=True)
def webhook():
    """Meta Lead Ads webhook endpoint.

    Meta uses GET for verification (hub.challenge handshake) and POST for
    actual lead notifications. We handle both here.
    """
    method = (frappe.request.method or "").upper()
    if method == "GET":
        return _handle_verification()
    if method == "POST":
        return _handle_lead_post()
    frappe.local.response["http_status_code"] = 405
    return {"status": "method_not_allowed"}


def _handle_verification():
    """Meta sends `hub.mode=subscribe&hub.challenge=X&hub.verify_token=Y`
    on initial webhook configuration. We echo `hub.challenge` if the
    verify_token matches our configured value."""
    expected_token = frappe.conf.get("meta_verify_token") or ""
    mode = frappe.form_dict.get("hub.mode")
    challenge = frappe.form_dict.get("hub.challenge")
    token = frappe.form_dict.get("hub.verify_token")

    if mode == "subscribe" and token and token == expected_token:
        # Meta expects the raw challenge string, not JSON.
        frappe.response["type"] = "raw"
        frappe.response["content"] = challenge or ""
        return
    frappe.local.response["http_status_code"] = 403
    return {"status": "verify_token_mismatch"}


def _handle_lead_post():
    raw_body = frappe.request.get_data() or b""
    signature = frappe.get_request_header("X-Hub-Signature-256") or ""

    if not _verify_meta_signature(raw_body, signature):
        frappe.local.response["http_status_code"] = 400
        return {"status": "invalid_signature"}

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        frappe.local.response["http_status_code"] = 400
        return {"status": "bad_json"}

    created = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            leadgen_id = value.get("leadgen_id")
            page_id = value.get("page_id")
            form_id = value.get("form_id")
            if not leadgen_id:
                continue
            try:
                lead_doc = _ingest_lead(leadgen_id, page_id, form_id)
                if lead_doc:
                    created.append(lead_doc.name)
            except Exception as e:
                frappe.log_error(f"Meta lead ingest failed: {e}", "boonxpress_crm.meta_leads")

    frappe.db.commit()
    return {"status": "ok", "leads_created": created}


def _verify_meta_signature(raw_body, signature):
    """Meta's `X-Hub-Signature-256` is `sha256=<hexhmac>`."""
    secret = frappe.conf.get("meta_app_secret") or ""
    if not secret or not signature:
        return False
    if "=" not in signature:
        return False
    algo, sig_hex = signature.split("=", 1)
    if algo != "sha256":
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_hex)


def _ingest_lead(leadgen_id, page_id, form_id):
    """Fetch the lead from Meta Graph API and create a CRM Lead.

    NOTE: requires `meta_page_access_token` in site config. If absent
    we still create a stub Lead with the leadgen_id so nothing is lost.
    """
    fields = _fetch_lead_from_graph(leadgen_id) or {}
    field_map = _resolve_field_map()

    lead_payload = {
        "doctype": "CRM Lead",
        "status": "New",
        "source": "Facebook Ads",
        "lead_owner": "Administrator",
    }

    # Meta returns `field_data` as a list of {name, values} dicts.
    for field_obj in fields.get("field_data", []) or []:
        meta_name = (field_obj.get("name") or "").lower()
        values = field_obj.get("values") or []
        crm_field = field_map.get(meta_name)
        if crm_field and values:
            lead_payload[crm_field] = values[0]

    # Fallback names if Meta didn't provide first_name/last_name separately.
    if "lead_name" in lead_payload and "first_name" not in lead_payload:
        parts = (lead_payload.get("lead_name") or "").split(maxsplit=1)
        lead_payload["first_name"] = parts[0] if parts else ""
        if len(parts) > 1:
            lead_payload["last_name"] = parts[1]

    # Tag the lead with Meta's identifiers so we can dedupe + audit.
    notes = f"Meta leadgen_id={leadgen_id}, page_id={page_id}, form_id={form_id}"
    lead_payload["lead_name"] = lead_payload.get("lead_name") or _compose_name(lead_payload)
    lead_payload["notes"] = notes

    if not lead_payload.get("first_name") and not lead_payload.get("mobile_no") and not lead_payload.get("email"):
        return None  # Empty payload — skip rather than create useless stub.

    doc = frappe.get_doc(lead_payload)
    doc.insert(ignore_permissions=True)
    return doc


def _resolve_field_map():
    """Per-tenant field map merged on top of defaults."""
    site_map = {}
    try:
        if frappe.db.exists("DocType", "Boon Tenant Config"):
            cfg = frappe.get_single("Boon Tenant Config")
            raw = getattr(cfg, "meta_lead_field_map", None)
            if raw:
                site_map = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except Exception:
        site_map = {}
    return {**DEFAULT_FIELD_MAP, **site_map}


def _fetch_lead_from_graph(leadgen_id):
    """Pull the lead's field_data from Meta's Graph API."""
    token = frappe.conf.get("meta_page_access_token") or ""
    if not token:
        return None
    import urllib.parse
    import urllib.request

    url = f"https://graph.facebook.com/v20.0/{leadgen_id}?{urllib.parse.urlencode({'access_token': token})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        frappe.log_error(f"Meta Graph fetch failed for leadgen {leadgen_id}: {e}", "boonxpress_crm.meta_leads")
        return None


def _compose_name(payload):
    parts = [payload.get("first_name") or "", payload.get("last_name") or ""]
    return " ".join(p for p in parts if p) or payload.get("email") or "Meta Lead"
