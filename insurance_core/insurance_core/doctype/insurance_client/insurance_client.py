import frappe
from frappe.model.document import Document
from frappe.utils import flt


class InsuranceClient(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if not self.lifecycle_stage:
			self.lifecycle_stage = "Prospect"
		if self.kyc_status == "Verified" and self.lifecycle_stage == "Prospect":
			self.lifecycle_stage = "Qualified"

	def on_update(self):
		if hasattr(self, "sync_linked_apps"):
			self.sync_linked_apps()
		self.flag_high_value()

	def flag_high_value(self):
		total = flt_premium(self.name)
		if total and total >= 100000 and not self.high_value:
			self.db_set("high_value", 1, update_modified=False)


def flt_premium(client):
	val = frappe.db.sql(
		"""
		select coalesce(sum(total_premium), 0) from `tabInsurance Policy`
		where client = %s and status in ('Active', 'Claimed', 'Settled', 'Grace Period')
		""",
		(client,),
	)
	return flt(val[0][0]) if val else 0
