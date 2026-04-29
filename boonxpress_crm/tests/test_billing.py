"""Tests for boonxpress_crm.api.billing — signature verification + cap.

Live Razorpay webhook delivery requires real merchant credentials and
isn't testable without them. Here we cover the parts that ARE pure code:
HMAC signature verification, event dispatch, and 5-user cap enforcement.
"""

import hashlib
import hmac
import json

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.billing import (
    _verify_razorpay_signature,
    enforce_user_cap,
    HANDLED_EVENTS,
)


class TestRazorpaySignature(FrappeTestCase):
    """HMAC-SHA256 signature verification matches Razorpay's spec."""

    def setUp(self):
        super().setUp()
        self._original_secret = frappe.conf.get("razorpay_webhook_secret")
        frappe.conf["razorpay_webhook_secret"] = "test_webhook_secret_v1"

    def tearDown(self):
        if self._original_secret is None:
            frappe.conf.pop("razorpay_webhook_secret", None)
        else:
            frappe.conf["razorpay_webhook_secret"] = self._original_secret
        super().tearDown()

    def test_valid_signature_passes(self):
        body = b'{"event": "subscription.activated"}'
        secret = "test_webhook_secret_v1".encode("utf-8")
        sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
        self.assertTrue(_verify_razorpay_signature(body, sig))

    def test_tampered_body_rejected(self):
        body = b'{"event": "subscription.activated"}'
        secret = "test_webhook_secret_v1".encode("utf-8")
        sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
        tampered = b'{"event": "subscription.cancelled"}'
        self.assertFalse(_verify_razorpay_signature(tampered, sig))

    def test_wrong_secret_rejected(self):
        body = b'{"event": "subscription.activated"}'
        wrong_sig = hmac.new(b"wrong_secret", body, hashlib.sha256).hexdigest()
        self.assertFalse(_verify_razorpay_signature(body, wrong_sig))

    def test_missing_signature_rejected(self):
        self.assertFalse(_verify_razorpay_signature(b"{}", ""))

    def test_missing_secret_rejected(self):
        frappe.conf.pop("razorpay_webhook_secret", None)
        body = b"{}"
        sig = hmac.new(b"anything", body, hashlib.sha256).hexdigest()
        self.assertFalse(_verify_razorpay_signature(body, sig))

    def test_handled_events_includes_lifecycle(self):
        # Spec sanity: every event we promise to handle in the docstring is in the set
        for evt in (
            "subscription.activated",
            "subscription.charged",
            "subscription.cancelled",
            "payment.failed",
        ):
            self.assertIn(evt, HANDLED_EVENTS)


class TestUserCap(FrappeTestCase):
    """5-user cap enforcement (PRD §3.3)."""

    def setUp(self):
        super().setUp()
        self._original_cap = frappe.conf.get("max_users")
        frappe.conf["max_users"] = 3  # Lower cap for tests

    def tearDown(self):
        if self._original_cap is None:
            frappe.conf.pop("max_users", None)
        else:
            frappe.conf["max_users"] = self._original_cap
        super().tearDown()

    def test_admin_and_guest_skip_cap(self):
        # The cap should never block built-in users
        for name in ("Administrator", "Guest"):
            doc = frappe.get_doc({
                "doctype": "User",
                "name": name,
                "user_type": "System User",
                "enabled": 1,
            })
            # Should not raise
            enforce_user_cap(doc)

    def test_website_user_skips_cap(self):
        doc = frappe.get_doc({
            "doctype": "User",
            "name": "siteguest@example.com",
            "user_type": "Website User",
            "enabled": 1,
        })
        # Website users don't count toward the cap
        enforce_user_cap(doc)

    def test_system_user_blocked_at_cap(self):
        # Only run this if there are already 3+ active System Users on the test site.
        # On most fresh test sites there's just Administrator (=1), so this test
        # configures the conf to reflect that and verifies the LOGIC runs without
        # crashing rather than asserting a throw — actual block behavior is
        # exercised on a populated tenant during Wave 6 manual smoke.
        active = frappe.db.count("User", filters={"enabled": 1, "user_type": "System User"})
        frappe.conf["max_users"] = max(1, active)  # Force the next insert to hit cap
        doc = frappe.get_doc({
            "doctype": "User",
            "first_name": "Capped",
            "email": "capped@example.com",
            "user_type": "System User",
            "enabled": 1,
        })
        with self.assertRaises(frappe.ValidationError):
            enforce_user_cap(doc)
