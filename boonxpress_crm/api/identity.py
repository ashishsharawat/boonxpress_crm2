"""Person identity resolver — collapses Lead/Deal/Contact into one canonical view.

Public entry point: `resolve(id)` accepts a CRM Lead, CRM Deal, or Contact name
and returns the unified Person dict consumed by the PCRM mobile UI.
"""

import frappe
from frappe import _


@frappe.whitelist()
def resolve(id):
    """Given any CRM Lead, CRM Deal, or Contact name, return the canonical Person.

    Returns:
        {
            "canonical_id": str,
            "lead": dict | None,
            "deals": list[dict],
            "contact": dict | None,
            "organization": dict | None,
            "summary": {
                "last_contact": str | None,
                "lifetime_value": float,
                "pipeline_value": float,
                "visit_count": int,
                "conversion_date": str | None,
            }
        }

    Raises frappe.DoesNotExistError if no record matches the given id.
    """
    if not id:
        frappe.throw(_("ID is required"))

    lead = None
    deals = []
    contact = None
    organization = None

    if id.startswith("CRM-LEAD-"):
        lead = _safe_get("CRM Lead", id)
        if not lead:
            frappe.throw(_("Person not found: {0}").format(id), exc=frappe.DoesNotExistError)
        deals = _deals_for_lead(lead)
        if deals:
            contact = _contact_from_deal(deals[0])
            organization = _organization_from_deal(deals[0])
    elif id.startswith("CRM-DEAL-"):
        deal = _safe_get("CRM Deal", id)
        if not deal:
            frappe.throw(_("Person not found: {0}").format(id), exc=frappe.DoesNotExistError)
        deals = [deal]
        contact = _contact_from_deal(deal)
        organization = _organization_from_deal(deal)
        lead = _lead_from_deal(deal)
        # Pull all other deals tied to the same contact
        if contact:
            deals = _deals_for_contact(contact["name"])
    else:
        # Try Contact
        contact = _safe_get("Contact", id)
        if not contact:
            frappe.throw(_("Person not found: {0}").format(id), exc=frappe.DoesNotExistError)
        deals = _deals_for_contact(contact["name"])
        if deals:
            organization = _organization_from_deal(deals[0])
            lead = _lead_from_deals(deals)

    canonical_id = (
        (contact and contact["name"])
        or (deals[0]["name"] if deals else None)
        or (lead and lead["name"])
    )

    return {
        "canonical_id": canonical_id,
        "lead": lead,
        "deals": deals,
        "contact": contact,
        "organization": organization,
        "summary": _compute_summary(lead, deals, contact),
    }


def _safe_get(doctype, name):
    if not frappe.db.exists(doctype, name):
        return None
    return frappe.get_doc(doctype, name).as_dict()


def _deals_for_lead(lead):
    if not lead:
        return []
    deal_names = frappe.get_all("CRM Deal", filters={"lead": lead["name"]}, pluck="name")
    return [frappe.get_doc("CRM Deal", n).as_dict() for n in deal_names]


def _deals_for_contact(contact_name):
    rows = frappe.db.sql(
        """
        SELECT DISTINCT parent FROM `tabCRM Deal Contact`
        WHERE contact = %s
        """,
        (contact_name,),
        as_dict=False,
    )
    return [frappe.get_doc("CRM Deal", row[0]).as_dict() for row in rows]


def _contact_from_deal(deal):
    if not deal:
        return None
    contacts = deal.get("contacts") or []
    if not contacts:
        return None
    primary = next((c for c in contacts if c.get("is_primary")), contacts[0])
    return _safe_get("Contact", primary.get("contact"))


def _organization_from_deal(deal):
    if not deal or not deal.get("organization"):
        return None
    return _safe_get("CRM Organization", deal["organization"])


def _lead_from_deal(deal):
    if not deal or not deal.get("lead"):
        return None
    return _safe_get("CRM Lead", deal["lead"])


def _lead_from_deals(deals):
    for d in deals:
        if d.get("lead"):
            return _safe_get("CRM Lead", d["lead"])
    return None


def _compute_summary(lead, deals, contact):
    pipeline_value = sum(
        float(d.get("deal_value") or 0)
        for d in deals
        if d.get("status") not in ("Won", "Lost")
    )
    lifetime_value = sum(
        float(d.get("deal_value") or 0)
        for d in deals
        if d.get("status") == "Won"
    )
    visit_count = len(deals)

    # Filter modified values into a list before max() — empty generator would raise ValueError
    deal_modifieds = [d.get("modified") for d in deals if d.get("modified")]
    last_contact = None
    if contact and contact.get("modified"):
        last_contact = str(contact["modified"])
    elif deal_modifieds:
        last_contact = str(max(deal_modifieds))
    elif lead and lead.get("modified"):
        last_contact = str(lead["modified"])

    conversion_date = None
    for d in deals:
        if d.get("status") == "Won" and d.get("modified"):
            conversion_date = str(d["modified"])
            break

    return {
        "last_contact": last_contact,
        "lifetime_value": lifetime_value,
        "pipeline_value": pipeline_value,
        "visit_count": visit_count,
        "conversion_date": conversion_date,
    }
