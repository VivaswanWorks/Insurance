import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class CommissionPayout(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_status_transition()

	def set_missing_values(self):
		if self.policy and not self.premium_amount:
			self.premium_amount = frappe.db.get_value("Insurance Policy", self.policy, "premium_amount")
		if self.premium_amount and self.rate is not None and not self.amount:
			self.amount = flt(self.premium_amount) * flt(self.rate) / 100.0
		if self.status == "Paid" and not self.payout_date:
			self.payout_date = nowdate()

	def validate_status_transition(self):
		if self.is_new():
			return
		old = self.get_db_value("status")
		if old == self.status:
			return
		allowed = {
			"Accrued": {"Approved", "Paid", "Cancelled"},
			"Approved": {"Paid", "Cancelled"},
			"Paid": set(),
			"Cancelled": set(),
		}
		if self.status not in allowed.get(old, {self.status}):
			frappe.throw(
				_("Cannot change payout status from {0} to {1}.").format(old, self.status),
				title=_("Invalid Status Transition"),
			)
