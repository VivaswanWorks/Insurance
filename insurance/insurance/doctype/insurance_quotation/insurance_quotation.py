import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, nowdate

from insurance.premium import calculate_premium as _calculate_premium


class InsuranceQuotation(Document):
	def validate(self):
		self.set_missing_values()
		self.recalculate()

	def set_missing_values(self):
		if self.scheme and not self.provider:
			self.provider = frappe.db.get_value("Insurance Scheme", self.scheme, "provider")
		if not self.valid_upto:
			self.valid_upto = add_days(nowdate(), 15)
		if not self.members:
			self.members = 1

	def recalculate(self):
		if not self.scheme:
			return
		result = _calculate_premium(
			self.scheme,
			age=cint(self.age),
			sum_insured=self.sum_insured,
			members=cint(self.members) or 1,
			quotation=self.name,
			log=bool(self.name),
		)
		self.net_premium = result["net_premium"]
		self.tax_amount = result["tax_amount"]
		self.total_premium = result["total_premium"]
		self.breakdown = result["breakdown"]


@frappe.whitelist()
def convert_to_policy(quotation):
	src = frappe.get_doc("Insurance Quotation", quotation)
	if src.status == "Converted" and src.converted_policy:
		return src.converted_policy
	if not src.client or not src.scheme:
		frappe.throw(_("Quotation needs a client and scheme before conversion."), title=_("Incomplete Quotation"))
	policy = frappe.get_doc({
		"doctype": "Insurance Policy",
		"policy_number": f"POL-{src.quotation_number or src.name}",
		"client": src.client,
		"scheme": src.scheme,
		"provider": src.provider,
		"policy_type": "New Business",
		"coverage_level": "Standard",
		"sum_assured": src.sum_insured,
		"premium_amount": src.net_premium,
		"tax_amount": src.tax_amount,
		"total_premium": src.total_premium,
		"premium_frequency": frappe.db.get_value("Insurance Scheme", src.scheme, "premium_frequency") or "Annually",
		"start_date": nowdate(),
		"status": "Draft",
		"quotation": src.name,
		"proposal_number": src.quotation_number or src.name,
	})
	policy.insert()
	src.db_set("converted_policy", policy.name)
	src.db_set("status", "Converted")
	if src.client:
		frappe.db.set_value("Insurance Client", src.client, "lifecycle_stage", "Policyholder")
	return policy.name
