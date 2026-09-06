import frappe
from frappe import _
from frappe.model.document import Document



class InsuranceOpportunity(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if self.client and not self.party:
			self.party = frappe.db.get_value("Insurance Client", self.client, "full_name")

	def on_update(self):
		if self.stage == "Won" and self.client:
			frappe.db.set_value("Insurance Client", self.client, "lifecycle_stage", "Quoted")
		if self.stage == "Quote Sent" and self.client:
			frappe.db.set_value("Insurance Client", self.client, "lifecycle_stage", "Quoted")


@frappe.whitelist()
def create_quotation(opportunity):
	src = frappe.get_doc("Insurance Opportunity", opportunity)
	if not src.insurance_scheme:
		frappe.throw(_("Select an interested scheme first."), title=_("Missing Scheme"))
	qtn = frappe.get_doc({
		"doctype": "Insurance Quotation",
		"quotation_number": f"QTN-{src.name}",
		"client": src.client,
		"scheme": src.insurance_scheme,
		"sum_insured": src.expected_premium or 0,
		"age": 35,
		"status": "Draft",
	})
	qtn.insert()
	src.db_set("converted_quotation", qtn.name)
	src.db_set("stage", "Quote Sent")
	return qtn.name
