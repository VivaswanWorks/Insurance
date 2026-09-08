import frappe
from frappe.tests.utils import FrappeTestCase


class TestClaimEligibilityEvaluation(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Claim Eligibility Evaluation"))
