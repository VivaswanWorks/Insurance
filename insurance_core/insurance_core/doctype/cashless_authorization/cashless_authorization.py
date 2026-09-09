import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from insurance_core.cashless import resolve_tpa, validate_cashless_hospital


class CashlessAuthorization(Document):
	def validate(self):
		self.set_missing_values()
		validate_cashless_hospital(self.hospital, throw=True)
		if flt(self.requested_amount) <= 0:
			frappe.throw(_("Requested amount must be greater than zero."))
		if self.status == "Approved" and not flt(self.approved_amount):
			self.approved_amount = self.requested_amount
		if self.status == "Utilized" and not flt(self.utilized_amount):
			self.utilized_amount = self.approved_amount or self.requested_amount

	def set_missing_values(self):
		if not self.request_date:
			self.request_date = nowdate()
		if self.claim and frappe.db.exists("Insurance Claim", self.claim):
			claim = frappe.db.get_value(
				"Insurance Claim",
				self.claim,
				["policy", "client", "provider", "hospital", "admission_date", "diagnosis", "claimed_amount"],
				as_dict=True,
			)
			if claim:
				self.policy = self.policy or claim.policy
				self.client = self.client or claim.client
				self.provider = self.provider or claim.provider
				self.hospital = self.hospital or claim.hospital
				self.admission_date = self.admission_date or claim.admission_date
				self.diagnosis = self.diagnosis or claim.diagnosis
				if not self.requested_amount:
					self.requested_amount = claim.claimed_amount
		if not self.tpa:
			self.tpa = resolve_tpa(hospital=self.hospital, provider=self.provider)
