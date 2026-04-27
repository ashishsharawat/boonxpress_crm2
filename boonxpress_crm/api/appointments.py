import frappe
from frappe import _


@frappe.whitelist()
def get_today():
    """Get today's appointments ordered by time slot."""
    today = frappe.utils.today()

    if not frappe.db.exists("DocType", "Boon Appointment"):
        return []

    appointments = frappe.get_all(
        "Boon Appointment",
        filters={"date": today, "status": ["!=", "Cancelled"]},
        fields=["name", "client", "client_name", "client_phone", "service_type", "time_slot", "date", "status", "staff"],
        order_by="time_slot asc"
    )

    return appointments


@frappe.whitelist()
def get_appointments(date=None, status=None, start=0, page_length=25):
    """Get appointments with optional filters."""
    if not frappe.db.exists("DocType", "Boon Appointment"):
        return []

    filters = {}
    if date:
        filters["date"] = date
    if status:
        filters["status"] = status

    return frappe.get_all(
        "Boon Appointment",
        filters=filters,
        fields=["name", "client", "client_name", "client_phone", "service_type", "time_slot", "date", "status", "staff"],
        order_by="date desc, time_slot asc",
        start=int(start),
        page_length=int(page_length)
    )


@frappe.whitelist()
def send_appointment_reminders():
    """Send WhatsApp reminders for tomorrow's appointments.

    Called hourly by scheduler. Only sends between 9 AM and 10 AM.
    """
    import datetime

    now = frappe.utils.now_datetime()
    if now.hour != 9:  # Only run at 9 AM
        return

    if not frappe.db.exists("DocType", "Boon Appointment"):
        return

    tomorrow = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    appointments = frappe.get_all(
        "Boon Appointment",
        filters={"date": tomorrow, "status": "Confirmed"},
        fields=["name", "client_name", "client_phone", "service_type", "time_slot"]
    )

    for apt in appointments:
        if apt.client_phone:
            # TODO: Integrate with frappe_whatsapp to send reminder
            frappe.log_error(
                f"Reminder due for {apt.client_name} at {apt.time_slot} for {apt.service_type}",
                "Appointment Reminder"
            )
