import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ClaimRecovery(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Recovery amount must be greater than zero."), title=_("Invalid Amount"))
		if self.status == "Recovered" and not self.recovered_on:
			self.recovered_on = nowdate()
		if self.recovery_type == "Reinsurance" and self.claim:
			# keep claim.reinsurance_recovery in sync when recovered amount changes
			if frappe.db.exists("Insurance Claim", self.claim):
				meta = frappe.get_meta("Insurance Claim")
				if meta.has_field("reinsurance_recovery"):
					frappe.db.set_value(
						"Insurance Claim",
						self.claim,
						"reinsurance_recovery",
						flt(self.amount),
						update_modified=False,
					)
