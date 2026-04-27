"""Shared test fixtures for boonxpress_crm.

Fixtures here are used by FrappeTestCase subclasses. Frappe's test
runner sets up the test site automatically; we add CRM-specific
fixtures (lead, deal, contact factories) here.
"""

import frappe


def make_lead(**overrides):
    """Insert a CRM Lead with sensible defaults; return the doc."""
    defaults = {
        "doctype": "CRM Lead",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "mobile_no": "+919999900001",
        "status": "Open",
    }
    defaults.update(overrides)
    doc = frappe.get_doc(defaults)
    doc.insert(ignore_permissions=True)
    return doc


def make_deal(lead_doc=None, **overrides):
    """Convert a lead → deal, or create a standalone deal."""
    if lead_doc:
        deal_name = lead_doc.convert_to_deal()
        return frappe.get_doc("CRM Deal", deal_name)
    defaults = {
        "doctype": "CRM Deal",
        "organization": "Test Org",
        "deal_value": 1000,
        "currency": "INR",
        "status": "Qualification",
    }
    defaults.update(overrides)
    doc = frappe.get_doc(defaults)
    doc.insert(ignore_permissions=True)
    return doc


def cleanup_test_records():
    """Remove any test data left behind."""
    for doctype in ["CRM Deal", "CRM Lead", "Contact", "CRM Organization"]:
        frappe.db.sql(f"DELETE FROM `tab{doctype}` WHERE owner='Administrator' AND name LIKE '%test%'")
    frappe.db.commit()
