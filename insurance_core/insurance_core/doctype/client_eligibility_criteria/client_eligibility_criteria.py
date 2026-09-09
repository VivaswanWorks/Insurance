import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class ClientEligibilityCriteria(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_scope()
		self.validate_logic()
		self.validate_weightage()

	def set_missing_values(self):
		if self.criteria_code:
			self.criteria_code = self.criteria_code.strip().upper().replace(" ", "_")
		if not self.status:
			self.status = "Active"
		if not self.evaluation_stage:
			self.evaluation_stage = "Claim Intake"
		if not self.claim_type:
			self.claim_type = "All"
		if not self.severity:
			self.severity = "Medium"
		if not self.failure_action:
			self.failure_action = "Block Submission" if self.is_mandatory else "Warning Only"

	def validate_scope(self):
		if self.applies_to == "Specific Scheme Type" and not self.scheme_type:
			frappe.throw(_("Scheme Type is required when Applies To is Specific Scheme Type."), title=_("Missing Scheme Type"))
		if self.applies_to == "Specific Scheme" and not self.insurance_scheme:
			frappe.throw(_("Insurance Scheme is required when Applies To is Specific Scheme."), title=_("Missing Scheme"))
		if self.applies_to == "Specific Provider" and not self.insurance_provider:
			frappe.throw(_("Insurance Provider is required when Applies To is Specific Provider."), title=_("Missing Provider"))
		if self.applies_to != "Specific Scheme Type":
			self.scheme_type = None
		if self.applies_to != "Specific Scheme":
			self.insurance_scheme = None
		if self.applies_to != "Specific Provider":
			self.insurance_provider = None
		if self.failure_action != "Require Override":
			self.override_role = None
		if self.failure_action == "Require Override" and not self.override_role:
			frappe.throw(_("Override Allowed For Role is required when Failure Action is Require Override."), title=_("Missing Override Role"))

	def validate_logic(self):
		method = self.evaluation_method
		if method == "Field Check":
			if not self.source_doctype or not self.field_to_check:
				frappe.throw(_("Source DocType and Field to Check are required for Field Check."), title=_("Incomplete Field Check"))
			if not self.operator:
				frappe.throw(_("Operator is required for Field Check."), title=_("Missing Operator"))
		elif method == "Expression" and not self.python_expression:
			frappe.throw(_("Python Expression is required for Expression evaluation."), title=_("Missing Expression"))
		elif method == "Script" and not self.custom_script:
			frappe.throw(_("Custom Script Path is required for Script evaluation."), title=_("Missing Script"))
		elif method == "External API" and not self.external_api:
			frappe.throw(_("External API Endpoint is required for External API evaluation."), title=_("Missing API"))
		elif method == "Checklist" and not self.get("checklist_items"):
			frappe.throw(_("Add at least one checklist item for Checklist evaluation."), title=_("Empty Checklist"))

	def validate_weightage(self):
		if flt(self.weightage) < 0 or flt(self.weightage) > 100:
			frappe.throw(_("Weightage must be between 0 and 100."), title=_("Invalid Weightage"))
		if self.pass_score is not None and self.pass_score != "" and (flt(self.pass_score) < 0 or flt(self.pass_score) > 100):
			frappe.throw(_("Minimum Pass Score must be between 0 and 100."), title=_("Invalid Pass Score"))

	def on_trash(self):
		if self.is_system:
			frappe.throw(_("System criteria cannot be deleted. Set Status to Inactive instead."), title=_("Protected Criteria"))

	def before_save(self):
		if not self.meta.has_field("criteria_version"):
			return
		self.criteria_version = cint(self.criteria_version) + 1 if not self.is_new() else cint(self.criteria_version) or 1

	def on_update(self):
		from insurance_core.eligibility import clear_criteria_cache

		clear_criteria_cache()

	def after_insert(self):
		from insurance_core.eligibility import clear_criteria_cache

		clear_criteria_cache()


def get_applicable_criteria(scheme=None, claim_type=None, provider=None, evaluation_stage="Claim Intake"):
	from insurance_core.eligibility import get_applicable_criteria as _fn

	return _fn(scheme=scheme, claim_type=claim_type, provider=provider, evaluation_stage=evaluation_stage)
