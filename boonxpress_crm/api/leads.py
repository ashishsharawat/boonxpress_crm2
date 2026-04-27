"""Helpers for the unified Leads tab — Closed segment specifically.

The Closed segment is a union of Lost CRM Leads + Lost CRM Deals.
Won deals are intentionally excluded — they "graduate" out of the Leads
tab and live exclusively in the Clients tab per the data-model UX spec.
"""

import frappe


# Subset of CRM Lead fields the Leads list view needs to render a row.
# `lead_name` is a virtual / computed field on Frappe CRM Lead; in some
# installations it is not selectable via `get_all`. We pull the underlying
# name parts and let the frontend compose if needed.
_LEAD_FIELDS = [
    "name",
    "first_name",
    "last_name",
    "mobile_no",
    "status",
    "modified",
]

_DEAL_FIELDS = [
    "name",
    "organization",
    "deal_value",
    "currency",
    "status",
    "modified",
]


@frappe.whitelist()
def get_closed(page=0, page_size=20):
    """Return a paginated union of Lost CRM Leads + Lost CRM Deals.

    Sorted by `modified desc`. Won deals are excluded (they graduate to Clients).

    Returns:
        { "items": list[dict], "has_more": bool, "page": int }
    """
    page = int(page or 0)
    page_size = int(page_size or 20)

    # Pull a generous window from each source, merge, sort, paginate.
    fetch_n = (page + 1) * page_size + page_size

    leads = frappe.get_all(
        "CRM Lead",
        filters={"status": ["in", ["Lost", "Junk"]]},
        fields=_LEAD_FIELDS,
        order_by="modified desc",
        limit_page_length=fetch_n,
    )
    deals = frappe.get_all(
        "CRM Deal",
        filters={"status": "Lost"},
        fields=_DEAL_FIELDS,
        order_by="modified desc",
        limit_page_length=fetch_n,
    )

    items = (
        [{"doctype": "CRM Lead", **r} for r in leads]
        + [{"doctype": "CRM Deal", **r} for r in deals]
    )
    items.sort(key=lambda r: r.get("modified") or "", reverse=True)

    start = page * page_size
    end = start + page_size
    page_items = items[start:end]
    has_more = len(items) > end

    return {"items": page_items, "has_more": has_more, "page": page}
