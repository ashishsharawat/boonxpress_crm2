"""Tests for boonxpress_crm.api.deals.transition_stage()."""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.deals import transition_stage
from boonxpress_crm.tests.conftest import make_lead, cleanup_test_records


class TestTransitionStage(FrappeTestCase):
    @classmethod
    def tearDownClass(cls):
        cleanup_test_records()
        super().tearDownClass()

    def test_transition_updates_status(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        result = transition_stage(deal_id=deal_name, new_status="Negotiation")
        self.assertEqual(result["status"], "Negotiation")
        deal = frappe.get_doc("CRM Deal", deal_name)
        self.assertEqual(deal.status, "Negotiation")

    def test_transition_with_note_creates_comment(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        transition_stage(deal_id=deal_name, new_status="Won", note="Great negotiation")
        comments = frappe.get_all(
            "Comment",
            filters={
                "reference_doctype": "CRM Deal",
                "reference_name": deal_name,
                "comment_type": "Comment",
            },
            fields=["content"],
        )
        self.assertTrue(any("Great negotiation" in c["content"] for c in comments))

    def test_invalid_status_rejected(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        with self.assertRaises(frappe.ValidationError):
            transition_stage(deal_id=deal_name, new_status="Bogus")
