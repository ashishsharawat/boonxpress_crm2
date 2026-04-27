"""Tests for boonxpress_crm.api.leads.get_closed()."""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.leads import get_closed
from boonxpress_crm.tests.conftest import make_lead, cleanup_test_records


class TestGetClosed(FrappeTestCase):
    @classmethod
    def tearDownClass(cls):
        cleanup_test_records()
        super().tearDownClass()

    def test_returns_shape(self):
        result = get_closed(page=0, page_size=20)
        self.assertIn("items", result)
        self.assertIn("has_more", result)
        self.assertIn("page", result)

    def test_includes_lost_lead(self):
        lead = make_lead(status="Junk")
        result = get_closed(page=0, page_size=100)
        names = [it["name"] for it in result["items"]]
        self.assertIn(lead.name, names)
        item = next(it for it in result["items"] if it["name"] == lead.name)
        self.assertEqual(item["doctype"], "CRM Lead")

    def test_includes_lost_deal(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        deal = frappe.get_doc("CRM Deal", deal_name)
        deal.status = "Lost"
        deal.save()
        result = get_closed(page=0, page_size=100)
        names = [it["name"] for it in result["items"]]
        self.assertIn(deal_name, names)

    def test_excludes_won_deal(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        deal = frappe.get_doc("CRM Deal", deal_name)
        deal.status = "Won"
        deal.save()
        result = get_closed(page=0, page_size=100)
        names = [it["name"] for it in result["items"]]
        self.assertNotIn(deal_name, names)
