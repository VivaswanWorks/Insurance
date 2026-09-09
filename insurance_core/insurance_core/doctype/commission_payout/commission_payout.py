import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CommissionPayout(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if self.policy and not self.premium_amount:
			self.premium_amount = frappe.db.get_value("Insurance Policy", self.policy, "premium_amount")
		if self.premium_amount and self.rate and not self.amount:
			self.amount = flt(self.premium_amount) * flt(self.rate) / 100.0
