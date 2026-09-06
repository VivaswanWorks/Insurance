import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class InsuranceProvider(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_license()
		self.validate_parent()

	def set_missing_values(self):
		if not self.provider_code and self.provider_id:
			self.provider_code = self.provider_id

	def validate_parent(self):
		if self.is_group and self.parent_provider:
			frappe.throw(_("A group provider cannot have a parent provider."), title=_("Invalid Hierarchy"))
		if self.parent_provider and self.parent_provider == self.name:
			frappe.throw(_("Provider cannot be its own parent."), title=_("Invalid Hierarchy"))

	def validate_license(self):
		if self.license_valid_upto and getdate(self.license_valid_upto) < getdate(nowdate()):
			if self.status == "Active":
				self.status = "Suspended"
				frappe.msgprint(
					_("License expired on {0}. Status set to Suspended.").format(self.license_valid_upto),
					title=_("License Expired"),
					indicator="orange",
				)

	def on_update(self):
		if self.status in ("Inactive", "Suspended"):
			self._inactivate_schemes()

	def _inactivate_schemes(self):
		schemes = frappe.get_all(
			"Insurance Scheme",
			filters={"provider": self.name, "status": "Active"},
			pluck="name",
		)
		for name in schemes:
			frappe.db.set_value("Insurance Scheme", name, "status", "Inactive")
		if schemes:
			frappe.msgprint(
				_("{0} active scheme(s) set to Inactive because the provider is {1}.").format(
					len(schemes), self.status
				),
				title=_("Schemes Updated"),
				indicator="orange",
			)


@frappe.whitelist()
def get_active_providers():
	return frappe.get_all(
		"Insurance Provider",
		filters={"status": "Active"},
		fields=["name", "legal_name", "brand_name", "provider_type", "provider_code"],
		order_by="legal_name",
	)
