"""Tests for boonxpress_crm.api.meta_leads — signature + payload mapping.

Real webhook delivery requires Meta App Secret + Page Access Token.
Here we test the parts that don't need them: signature verification
and field-mapping logic.
"""

import hashlib
import hmac
import json

import frappe
from frappe.tests.utils import FrappeTestCase

from boonxpress_crm.api.meta_leads import (
    _verify_meta_signature,
    _resolve_field_map,
    DEFAULT_FIELD_MAP,
)


class TestMetaSignature(FrappeTestCase):
    """X-Hub-Signature-256 verification matches Meta's webhook spec."""

    def setUp(self):
        super().setUp()
        self._original_secret = frappe.conf.get("meta_app_secret")
        frappe.conf["meta_app_secret"] = "meta_app_secret_test_v1"

    def tearDown(self):
        if self._original_secret is None:
            frappe.conf.pop("meta_app_secret", None)
        else:
            frappe.conf["meta_app_secret"] = self._original_secret
        super().tearDown()

    def _sign(self, body, secret=None):
        s = (secret or "meta_app_secret_test_v1").encode("utf-8")
        return "sha256=" + hmac.new(s, body, hashlib.sha256).hexdigest()

    def test_valid_signature_passes(self):
        body = b'{"object": "page"}'
        self.assertTrue(_verify_meta_signature(body, self._sign(body)))

    def test_tampered_body_rejected(self):
        body = b'{"object": "page"}'
        sig = self._sign(body)
        self.assertFalse(_verify_meta_signature(b'{"object": "tampered"}', sig))

    def test_wrong_secret_rejected(self):
        body = b'{"object": "page"}'
        sig = self._sign(body, secret="wrong_secret")
        self.assertFalse(_verify_meta_signature(body, sig))

    def test_missing_algo_prefix_rejected(self):
        body = b'{}'
        # Without the `sha256=` prefix the verifier should refuse
        self.assertFalse(_verify_meta_signature(body, "abc123"))

    def test_unsupported_algo_rejected(self):
        body = b'{}'
        self.assertFalse(_verify_meta_signature(body, "sha1=abc"))


class TestFieldMap(FrappeTestCase):
    """Default field map covers the common Meta lead form fields."""

    def test_defaults_include_phone_email_name(self):
        for meta_field in ("full_name", "first_name", "last_name", "email", "phone_number"):
            self.assertIn(meta_field, DEFAULT_FIELD_MAP)

    def test_resolve_returns_defaults_when_no_override(self):
        # Boon Tenant Config may or may not exist on the test site;
        # either way _resolve_field_map should return at least the defaults.
        result = _resolve_field_map()
        for key in DEFAULT_FIELD_MAP:
            self.assertIn(key, result)
