import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ClientKYC(Document):
	def validate(self):
		self.set_missing_values()
		if self.valid_upto and getdate(self.valid_upto) < getdate(nowdate()) and self.status == "Verified":
			self.status = "Expired"

	def set_missing_values(self):
		if self.status == "Verified" and not self.verified_on:
			self.verified_on = nowdate()

	def on_update(self):
		if self.client and self.status:
			mapping = {
				"Pending": "Pending",
				"Verified": "Verified",
				"Rejected": "Rejected",
				"Expired": "Pending",
			}
			frappe.db.set_value("Insurance Client", self.client, "kyc_status", mapping.get(self.status, self.status))
			if self.risk_category:
				frappe.db.set_value("Insurance Client", self.client, "risk_category", self.risk_category)
