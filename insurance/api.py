import json

import frappe
from frappe.utils import cint


@frappe.whitelist()
def check_app_permission():
	return bool(set(frappe.get_roles()) & {
		"System Manager",
		"Insurance Manager",
		"Insurance Agent",
		"Claims Adjuster",
		"Compliance Officer",
		"Insurance User",
	})


@frappe.whitelist()
def ping():
	return {"ok": True, "user": frappe.session.user, "roles": frappe.get_roles()}


@frappe.whitelist()
def calculate_premium(scheme, age=None, sum_insured=None, members=1, extras=None):
	from insurance.premium import calculate_premium as _calc

	if isinstance(extras, str):
		extras = json.loads(extras) if extras else {}
	return _calc(
		scheme,
		age=cint(age),
		sum_insured=sum_insured,
		members=cint(members) or 1,
		extras=extras or {},
	)


@frappe.whitelist()
def get_active_providers():
	from insurance.insurance.doctype.insurance_provider.insurance_provider import get_active_providers as _fn

	return _fn()


@frappe.whitelist()
def get_active_schemes(scheme_type=None):
	from insurance.insurance.doctype.insurance_scheme.insurance_scheme import get_active_schemes as _fn

	return _fn(scheme_type=scheme_type)


@frappe.whitelist()
def convert_quotation(quotation):
	from insurance.insurance.doctype.insurance_quotation.insurance_quotation import convert_to_policy

	return convert_to_policy(quotation)


@frappe.whitelist()
def create_renewal(policy):
	from insurance.insurance.doctype.insurance_policy.insurance_policy import create_renewal as _fn

	return _fn(policy)


@frappe.whitelist()
def apply_endorsement(name):
	from insurance.insurance.doctype.policy_endorsement.policy_endorsement import apply_endorsement as _fn

	return _fn(name)
