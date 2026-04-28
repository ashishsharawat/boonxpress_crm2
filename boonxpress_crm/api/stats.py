import frappe


@frappe.whitelist()
def get_quick_stats():
    """Get quick stats for the home screen dashboard.

    Returns counts relevant to the current vertical.
    """
    today = frappe.utils.today()

    stats = {}

    # Appointments today (if Boon Appointment DocType exists)
    if frappe.db.exists("DocType", "Boon Appointment"):
        stats["appointments_today"] = frappe.db.count(
            "Boon Appointment",
            filters={"date": today, "status": ["!=", "Cancelled"]}
        )
        stats["consultations_today"] = stats["appointments_today"]  # Alias for clinic
        stats["test_drives_today"] = stats["appointments_today"]  # Alias for auto
    else:
        stats["appointments_today"] = 0
        stats["consultations_today"] = 0
        stats["test_drives_today"] = 0

    # New leads (created today)
    stats["new_leads"] = frappe.db.count(
        "CRM Lead",
        filters={"creation": [">=", today]}
    )

    # Hot leads (for auto vertical) — "New" is Frappe CRM's seeded
    # initial Lead Status (no "Open" record exists by default).
    stats["hot_leads"] = frappe.db.count(
        "CRM Lead",
        filters={"status": "New"}
    )

    # Open deals
    if frappe.db.exists("DocType", "CRM Deal"):
        stats["open_deals"] = frappe.db.count(
            "CRM Deal",
            filters={"status": ["not in", ["Won", "Lost"]]}
        )
    else:
        stats["open_deals"] = 0

    # Pending orders (for retail)
    stats["pending_orders"] = stats.get("open_deals", 0)
    stats["new_enquiries"] = stats.get("new_leads", 0)

    # WhatsApp pending (placeholder -- requires frappe_whatsapp integration)
    stats["wa_pending"] = 0

    return stats


@frappe.whitelist()
def get_recent_activity(limit=3):
    """Tenant-wide recent activity preview for the home screen.

    Returns the N newest events across leads, deals, and appointments
    as plain summaries — not the full Activity-tab feed payload, just
    enough for an at-a-glance "what happened recently" card.
    """
    limit = max(1, min(int(limit or 3), 10))
    events = []

    leads = frappe.get_all(
        "CRM Lead",
        fields=["name", "first_name", "last_name", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )
    for lead in leads:
        full_name = f"{lead.get('first_name') or ''} {lead.get('last_name') or ''}".strip() or lead["name"]
        events.append({
            "id": lead["name"],
            "summary": f"New lead: {full_name}",
            "timestamp": str(lead["creation"]),
            "type": "lead",
        })

    if frappe.db.exists("DocType", "CRM Deal"):
        deals = frappe.get_all(
            "CRM Deal",
            fields=["name", "organization", "status", "modified"],
            order_by="modified desc",
            limit_page_length=limit,
        )
        for deal in deals:
            label = deal.get("organization") or deal["name"]
            events.append({
                "id": deal["name"],
                "summary": f"Deal {deal.get('status', '')}: {label}",
                "timestamp": str(deal["modified"]),
                "type": "deal",
            })

    if frappe.db.exists("DocType", "Boon Appointment"):
        appts = frappe.get_all(
            "Boon Appointment",
            fields=["name", "client_name", "service_type", "status", "modified"],
            order_by="modified desc",
            limit_page_length=limit,
        )
        for apt in appts:
            events.append({
                "id": apt["name"],
                "summary": f"Appointment: {apt.get('client_name', '')} — {apt.get('service_type', '')} ({apt.get('status', '')})",
                "timestamp": str(apt["modified"]),
                "type": "appointment",
            })

    events.sort(key=lambda e: e["timestamp"], reverse=True)
    return events[:limit]


@frappe.whitelist()
def get_notification_counts():
    """Get notification counts for the header badge."""
    today = frappe.utils.today()

    return {
        "wa_pending": 0,  # Placeholder
        "new_leads": frappe.db.count(
            "CRM Lead",
            filters={"creation": [">=", today], "_seen": ["not like", f"%{frappe.session.user}%"]}
        ) if frappe.db.has_column("CRM Lead", "_seen") else 0,
    }
