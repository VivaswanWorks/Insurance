import frappe
from frappe.tests.utils import FrappeTestCase


class TestCommissionRule(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Commission Rule"))
