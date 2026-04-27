"""Tests for boonxpress_crm.api.identity.resolve()."""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.identity import resolve
from boonxpress_crm.tests.conftest import make_lead, cleanup_test_records


class TestIdentityResolve(FrappeTestCase):
    @classmethod
    def tearDownClass(cls):
        cleanup_test_records()
        super().tearDownClass()

    def test_resolve_from_lead_id_returns_lead_only(self):
        lead = make_lead()
        result = resolve(lead.name)
        self.assertEqual(result["canonical_id"], lead.name)
        self.assertIsNotNone(result["lead"])
        self.assertEqual(result["lead"]["name"], lead.name)
        self.assertEqual(result["deals"], [])
        self.assertIsNone(result.get("contact"))

    def test_resolve_from_lead_after_conversion_returns_full_set(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        result = resolve(lead.name)
        self.assertEqual(len(result["deals"]), 1)
        self.assertEqual(result["deals"][0]["name"], deal_name)
        self.assertIsNotNone(result.get("contact"))

    def test_resolve_from_deal_id_finds_lead_and_contact(self):
        lead = make_lead()
        deal_name = lead.convert_to_deal()
        result = resolve(deal_name)
        self.assertEqual(len(result["deals"]), 1)
        self.assertIsNotNone(result.get("contact"))
        self.assertIsNotNone(result.get("lead"))

    def test_resolve_invalid_lead_id_raises(self):
        with self.assertRaises(frappe.DoesNotExistError):
            resolve("CRM-LEAD-2099-99999")

    def test_resolve_invalid_deal_id_raises(self):
        with self.assertRaises(frappe.DoesNotExistError):
            resolve("CRM-DEAL-2099-99999")

    def test_resolve_invalid_contact_id_raises(self):
        with self.assertRaises(frappe.DoesNotExistError):
            resolve("non-existent-contact-id-xyz")

    def test_resolve_summary_contains_required_keys(self):
        lead = make_lead()
        result = resolve(lead.name)
        self.assertIn("summary", result)
        for key in ("last_contact", "lifetime_value", "pipeline_value", "visit_count", "conversion_date"):
            self.assertIn(key, result["summary"])

    def test_resolve_summary_handles_deals_without_modified(self):
        # Regression: max() over empty filtered generator must not raise ValueError
        lead = make_lead()
        result = resolve(lead.name)
        # No deals — pipeline/lifetime should be 0, last_contact should fall back to lead.modified
        self.assertEqual(result["summary"]["pipeline_value"], 0)
        self.assertEqual(result["summary"]["lifetime_value"], 0)
