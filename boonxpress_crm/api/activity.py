"""Merged activity feed for a Person across Lead/Deal/Contact references.

Surfaces events from Communication, CRM Call Log, Comment, Version (Frappe's
audit log for status changes), CRM Task, and Boon Appointment as a single
chronological stream with optional filter-chip narrowing and cursor pagination.
"""

import json

import frappe

from boonxpress_crm.api.identity import resolve


EVENT_TYPE_MAP = {
    "messages": ["whatsapp", "email"],
    "calls": ["call"],
    "stage": ["stage"],
    "notes": ["note"],
    "appointments": ["appointment"],
    "tasks": ["task"],
    "files": ["file"],
}


@frappe.whitelist()
def get_feed(person_id, filter_type="all", page_cursor=None, page_size=50):
    """Return chronological merged events across linked Frappe doctypes.

    Args:
        person_id: lead/deal/contact name
        filter_type: one of 'all' | 'messages' | 'calls' | 'stage' | 'notes' | 'appointments' | 'tasks' | 'files'
        page_cursor: ISO datetime string — return events older than this
        page_size: int (max 100)

    Returns:
        { "events": [...], "next_cursor": str | None }
    """
    page_size = min(int(page_size or 50), 100)
    person = resolve(person_id)
    ref_names = _collect_reference_names(person)

    events = []
    events.extend(_fetch_comments(ref_names))
    events.extend(_fetch_communications(ref_names))
    events.extend(_fetch_call_logs(ref_names))
    events.extend(_fetch_status_changes(person))
    events.extend(_fetch_tasks(ref_names))
    events.extend(_fetch_appointments(person))

    if filter_type and filter_type != "all":
        allowed = EVENT_TYPE_MAP.get(filter_type, [])
        events = [e for e in events if e["type"] in allowed]

    events.sort(key=lambda e: e["timestamp"], reverse=True)

    if page_cursor:
        events = [e for e in events if e["timestamp"] < page_cursor]

    page = events[:page_size]
    next_cursor = page[-1]["timestamp"] if len(events) > page_size else None

    return {"events": page, "next_cursor": next_cursor}


def _collect_reference_names(person):
    refs = []
    if person.get("lead"):
        refs.append(("CRM Lead", person["lead"]["name"]))
    for d in person.get("deals", []):
        refs.append(("CRM Deal", d["name"]))
    if person.get("contact"):
        refs.append(("Contact", person["contact"]["name"]))
    return refs


def _fetch_comments(ref_names):
    if not ref_names:
        return []
    doctypes = list({r[0] for r in ref_names})
    names = list({r[1] for r in ref_names})
    rows = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": ["in", doctypes],
            "reference_name": ["in", names],
            "comment_type": "Comment",
        },
        fields=["name", "content", "creation", "owner", "reference_doctype", "reference_name"],
    )
    return [
        {
            "id": r["name"],
            "type": "note",
            "content": r["content"],
            "timestamp": str(r["creation"]),
            "owner": r["owner"],
            "source_doctype": r["reference_doctype"],
            "source_name": r["reference_name"],
        }
        for r in rows
    ]


def _fetch_communications(ref_names):
    """Emails and WhatsApp messages logged via Frappe's Communication doctype."""
    if not ref_names:
        return []
    doctypes = list({r[0] for r in ref_names})
    names = list({r[1] for r in ref_names})
    rows = frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": ["in", doctypes],
            "reference_name": ["in", names],
        },
        fields=["name", "content", "communication_medium", "sent_or_received", "creation", "subject"],
    )
    events = []
    for r in rows:
        medium = (r.get("communication_medium") or "").lower()
        if "whatsapp" in medium:
            event_type = "whatsapp"
        elif "email" in medium:
            event_type = "email"
        else:
            event_type = "note"
        events.append({
            "id": r["name"],
            "type": event_type,
            "direction": (r.get("sent_or_received") or "").lower(),
            "content": r.get("subject") or (r.get("content") or "")[:200],
            "timestamp": str(r["creation"]),
        })
    return events


def _fetch_call_logs(ref_names):
    if not ref_names:
        return []
    names = list({r[1] for r in ref_names})
    try:
        rows = frappe.get_all(
            "CRM Call Log",
            filters={"reference_docname": ["in", names]},
            fields=["name", "from", "to", "duration", "summary", "type", "creation"],
        )
    except Exception:
        # Field name varies across Frappe CRM versions
        return []
    return [
        {
            "id": r["name"],
            "type": "call",
            "direction": (r.get("type") or "").lower(),
            "content": f"{int(r.get('duration') or 0)}s — {r.get('summary') or ''}",
            "timestamp": str(r["creation"]),
        }
        for r in rows
    ]


def _fetch_status_changes(person):
    """Pull doc-state transitions from Frappe's Version audit log."""
    events = []
    targets = []
    if person.get("lead"):
        targets.append(("CRM Lead", person["lead"]["name"]))
    for d in person.get("deals", []):
        targets.append(("CRM Deal", d["name"]))

    for ref_doctype, ref_name in targets:
        versions = frappe.get_all(
            "Version",
            filters={"ref_doctype": ref_doctype, "docname": ref_name},
            fields=["name", "data", "creation", "owner"],
        )
        for v in versions:
            try:
                data = json.loads(v["data"] or "{}")
                for change in data.get("changed", []):
                    if len(change) >= 3 and change[0] == "status":
                        events.append({
                            "id": v["name"],
                            "type": "stage",
                            "content": f"{ref_doctype.replace('CRM ', '')}: {change[1]} → {change[2]}",
                            "timestamp": str(v["creation"]),
                            "owner": v["owner"],
                        })
            except (json.JSONDecodeError, IndexError, TypeError):
                continue
    return events


def _fetch_tasks(ref_names):
    if not ref_names:
        return []
    names = list({r[1] for r in ref_names})
    try:
        rows = frappe.get_all(
            "CRM Task",
            filters={"reference_docname": ["in", names]},
            fields=["name", "title", "status", "due_date", "creation"],
        )
    except Exception:
        return []
    return [
        {
            "id": r["name"],
            "type": "task",
            "content": f"Task: {r['title']} ({r['status']})",
            "timestamp": str(r["creation"]),
        }
        for r in rows
    ]


def _fetch_appointments(person):
    if not person.get("contact"):
        return []
    if not frappe.db.exists("DocType", "Boon Appointment"):
        return []
    rows = frappe.get_all(
        "Boon Appointment",
        filters={"customer": person["contact"]["name"]},
        fields=["name", "service", "start_time", "status", "total_amount", "creation"],
    )
    return [
        {
            "id": r["name"],
            "type": "appointment",
            "content": f"{r.get('service', '')} — {r.get('status', '')}",
            "timestamp": str(r.get("start_time") or r["creation"]),
            "amount": float(r.get("total_amount") or 0),
        }
        for r in rows
    ]
