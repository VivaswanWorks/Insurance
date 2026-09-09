import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

from insurance_core.premium import calculate_premium


class _Scheme:
	name = "TEST-SCH-PREM"
	premium_basis = "Age Band"
	gst_applicable = 1
	tax_gst_rate = 18
	minimum_sum_assured = 0
	premium_table = None
	loading_discount_rules = None

	def __init__(self):
		self.premium_table = [
			frappe._dict(
				age_from=18,
				age_to=40,
				sum_insured_from=0,
				sum_insured_to=1000000,
				premium_amount=10000,
				premium_rate=0,
				frequency="Yearly",
			)
		]
		self.loading_discount_rules = [
			frappe._dict(rule_type="Discount", criteria="ncb", percentage=10, amount=0, applicable_on="Premium")
		]

	def get(self, key, default=None):
		return getattr(self, key, default)


class TestInsuranceScheme(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "Insurance Scheme"))

	def test_premium_slab_and_discount(self):
		result = calculate_premium(_Scheme(), age=30, sum_insured=500000, members=1, extras={"ncb": True}, log=False)
		self.assertEqual(cint(result["net_premium"]), 9000)
		self.assertEqual(cint(result["tax_amount"]), 1620)
		self.assertEqual(cint(result["total_premium"]), 10620)
