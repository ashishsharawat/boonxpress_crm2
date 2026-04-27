"""Shared test fixtures for boonxpress_crm.

Fixtures here are used by FrappeTestCase subclasses. Frappe's test
runner wraps each test in a transaction that rolls back on tearDown,
so most cleanup is automatic. The factories below produce
collision-safe records (unique email + mobile per call) so multiple
inserts in one test class don't trip Frappe's unique constraints.

`cleanup_test_records()` is a defensive sweep for records that
escaped the rollback (e.g., when a test explicitly committed). It
matches only the `BOONTEST_PREFIX` so it cannot touch unrelated data.
"""

import frappe

# All factories tag their records with this prefix so cleanup is precise.
BOONTEST_PREFIX = "boontest"


def _unique_suffix():
    """Short random suffix for collision-free test data."""
    return frappe.generate_hash(length=8)


def make_lead(**overrides):
    """Insert a CRM Lead with collision-safe defaults; return the doc."""
    suffix = _unique_suffix()
    defaults = {
        "doctype": "CRM Lead",
        "first_name": f"{BOONTEST_PREFIX}_{suffix}",
        "last_name": "User",
        "email": f"{BOONTEST_PREFIX}+{suffix}@example.com",
        "mobile_no": f"+91999{suffix[:7]}",
        "status": "Open",
    }
    defaults.update(overrides)
    doc = frappe.get_doc(defaults)
    doc.insert(ignore_permissions=True)
    return doc


def make_deal(lead_doc=None, **overrides):
    """Convert a lead → deal, or create a standalone deal.

    When `lead_doc` is provided, `convert_to_deal()` produces the deal
    and `overrides` are applied on top of the converted doc and saved.
    """
    if lead_doc:
        deal_name = lead_doc.convert_to_deal()
        deal = frappe.get_doc("CRM Deal", deal_name)
        if overrides:
            for k, v in overrides.items():
                setattr(deal, k, v)
            deal.save(ignore_permissions=True)
        return deal

    suffix = _unique_suffix()
    defaults = {
        "doctype": "CRM Deal",
        "organization": f"{BOONTEST_PREFIX}_org_{suffix}",
        "deal_value": 1000,
        "currency": "INR",
        "status": "Qualification",
    }
    defaults.update(overrides)
    doc = frappe.get_doc(defaults)
    doc.insert(ignore_permissions=True)
    return doc


def cleanup_test_records():
    """Defensively delete records tagged with BOONTEST_PREFIX.

    `FrappeTestCase` already rolls back transactions after each test;
    this is a backstop for cases where a test explicitly committed.
    Order matters because of cross-doctype links: Deals first
    (reference Leads + Contacts + Organizations), then Contacts and
    Leads (Contact may exist independently of Lead post-conversion),
    then Organizations.
    """
    deletion_order = [
        ("CRM Deal", "organization"),
        ("Contact", "first_name"),
        ("CRM Lead", "first_name"),
        ("CRM Organization", "organization_name"),
    ]
    for doctype, match_field in deletion_order:
        names = frappe.get_all(
            doctype,
            filters={match_field: ["like", f"{BOONTEST_PREFIX}%"]},
            pluck="name",
        )
        for name in names:
            try:
                frappe.delete_doc(
                    doctype,
                    name,
                    force=True,
                    ignore_links=True,
                    delete_permanently=True,
                )
            except frappe.DoesNotExistError:
                continue
    frappe.db.commit()
