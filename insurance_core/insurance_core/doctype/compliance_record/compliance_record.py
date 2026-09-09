import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ComplianceRecord(Document):
	def validate(self):
		self.set_missing_values()
		if self.due_date and getdate(self.due_date) < getdate(nowdate()) and self.status not in (
			"Closed",
			"Approved",
			"Overdue",
		):
			self.status = "Overdue"

	def set_missing_values(self):
		if self.status == "Closed" and not self.closed_on:
			self.closed_on = nowdate()
