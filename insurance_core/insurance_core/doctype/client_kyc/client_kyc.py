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
			self.rescore_open_claims()

	def rescore_open_claims(self):
		if not self.client or not frappe.db.exists("DocType", "Insurance Claim"):
			return
		claims = frappe.get_all(
			"Insurance Claim",
			filters={
				"client": self.client,
				"status": ["in", ["Draft", "Submitted", "Under Review", "Documents Pending", "Additional Info Required"]],
			},
			pluck="name",
		)
		if not claims:
			return
		from insurance_core.eligibility import evaluate_claim_eligibility

		for name in claims:
			try:
				evaluate_claim_eligibility(name, throw=False)
			except Exception:
				frappe.log_error(title="Eligibility rescore after KYC update failed", message=name)
