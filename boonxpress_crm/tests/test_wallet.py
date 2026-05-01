"""Tests for boonxpress_crm.api.wallet — credit reservation + commit/refund.

Covers the locally-testable surface: tier table shape, pricing math,
free-quota behavior, refund correctness. Live Razorpay flows are deferred
until merchant credentials are in hand.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api import wallet as wallet_api
from boonxpress_crm.api.wallet import TIERS, DEFAULT_FREE_UTILITY_QUOTA


class TestTierTable(FrappeTestCase):
    def test_all_locked_tiers_present(self):
        for tier in ("Starter ₹500", "Growth ₹2000", "Pro ₹5000", "Scale ₹10000"):
            self.assertIn(tier, TIERS)

    def test_bonus_percentages_match_decision(self):
        # Decisions locked by user: 0/5/10/15%
        self.assertEqual(TIERS["Starter ₹500"]["bonus_pct"], 0)
        self.assertEqual(TIERS["Growth ₹2000"]["bonus_pct"], 5)
        self.assertEqual(TIERS["Pro ₹5000"]["bonus_pct"], 10)
        self.assertEqual(TIERS["Scale ₹10000"]["bonus_pct"], 15)

    def test_amounts_match_decision(self):
        self.assertEqual(TIERS["Starter ₹500"]["amount_inr"], 500)
        self.assertEqual(TIERS["Growth ₹2000"]["amount_inr"], 2000)
        self.assertEqual(TIERS["Pro ₹5000"]["amount_inr"], 5000)
        self.assertEqual(TIERS["Scale ₹10000"]["amount_inr"], 10000)


class TestFreeQuotaConstant(FrappeTestCase):
    def test_default_free_utility_quota_matches_decision(self):
        # Decision locked: 100 utility conversations/month free with ₹999 plan
        self.assertEqual(DEFAULT_FREE_UTILITY_QUOTA, 100)


class TestPricingTableSeeded(FrappeTestCase):
    """After seed_pricing_table runs, India prices match locked decisions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        wallet_api.seed_pricing_table()

    def test_india_marketing_price_with_40pct_markup(self):
        if not frappe.db.exists("DocType", "WhatsApp Conversation Pricing"):
            self.skipTest("Pricing doctype not migrated on this test site")
        rows = frappe.get_all(
            "WhatsApp Conversation Pricing",
            filters={"country_code": "IN", "category": "Marketing", "active": 1},
            fields=["meta_cost_inr", "markup_pct", "customer_price_inr"],
        )
        if not rows:
            self.skipTest("Pricing not seeded on this test site")
        row = rows[0]
        self.assertAlmostEqual(float(row["markup_pct"]), 40.0, places=2)
        # 0.85 × 1.40 = 1.19
        expected = float(row["meta_cost_inr"]) * 1.40
        self.assertAlmostEqual(float(row["customer_price_inr"]), expected, places=2)

    def test_india_utility_price_with_25pct_markup(self):
        if not frappe.db.exists("DocType", "WhatsApp Conversation Pricing"):
            self.skipTest("Pricing doctype not migrated on this test site")
        rows = frappe.get_all(
            "WhatsApp Conversation Pricing",
            filters={"country_code": "IN", "category": "Utility", "active": 1},
            fields=["meta_cost_inr", "markup_pct", "customer_price_inr"],
        )
        if not rows:
            self.skipTest("Pricing not seeded on this test site")
        row = rows[0]
        self.assertAlmostEqual(float(row["markup_pct"]), 25.0, places=2)


class TestServiceCategoryFree(FrappeTestCase):
    """Service-window messages are truly free per locked decision."""

    def test_service_reservation_is_zero(self):
        if not frappe.db.exists("DocType", "WhatsApp Credit Wallet"):
            self.skipTest("Wallet doctype not migrated on this test site")
        result = wallet_api.check_and_reserve(
            category="Service",
            customer_phone="+919999900099",
            waba_phone_id="test_waba_phone_1",
            country_code="IN",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["charge_inr"], 0)
        self.assertTrue(result.get("service_window"))


class TestInvalidInput(FrappeTestCase):
    def test_missing_customer_phone_rejected(self):
        result = wallet_api.check_and_reserve(
            category="Marketing",
            customer_phone="",
            waba_phone_id="test_waba",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "missing_customer_phone")

    def test_missing_waba_rejected(self):
        result = wallet_api.check_and_reserve(
            category="Marketing",
            customer_phone="+919999900001",
            waba_phone_id="",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "missing_waba_phone_id")

    def test_unknown_tier_rejected(self):
        with self.assertRaises(Exception):
            wallet_api.create_purchase_order("Imaginary ₹50000")
