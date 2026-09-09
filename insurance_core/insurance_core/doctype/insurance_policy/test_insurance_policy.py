import frappe
from frappe.tests.utils import FrappeTestCase


class TestInsurancePolicy(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Insurance Policy"))
