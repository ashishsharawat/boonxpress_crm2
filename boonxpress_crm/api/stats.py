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

    # Hot leads (for auto vertical)
    stats["hot_leads"] = frappe.db.count(
        "CRM Lead",
        filters={"status": "Open"}
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
