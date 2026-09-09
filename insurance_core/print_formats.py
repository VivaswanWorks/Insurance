"""Print / document generation helpers for Insurance Core.

Templates live under insurance_core/templates/print_formats/.
Use get_print_html(doctype, name, template) from desk buttons or portal.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import fmt_money, formatdate


TEMPLATE_MAP = {
	"Insurance Policy": "print_formats/policy_schedule.html",
	"Insurance Claim": "print_formats/claim_form.html",
	"claim_settlement": "print_formats/settlement_letter.html",
}


def _policy_context(name):
	policy = frappe.get_doc("Insurance Policy", name)
	client = frappe.get_doc("Insurance Client", policy.client) if policy.client else None
	scheme = frappe.get_doc("Insurance Scheme", policy.scheme) if policy.scheme else None
	provider = frappe.get_doc("Insurance Provider", policy.provider) if policy.provider else None
	return {
		"policy": policy,
		"client": client,
		"scheme": scheme,
		"provider": provider,
		"members": policy.get("policy_members") or [],
		"coverages": policy.get("policy_coverages") or [],
		"fmt_money": fmt_money,
		"formatdate": formatdate,
		"_": _,
	}


def _claim_context(name):
	claim = frappe.get_doc("Insurance Claim", name)
	policy = frappe.get_doc("Insurance Policy", claim.policy) if claim.policy else None
	client = frappe.get_doc("Insurance Client", claim.client) if claim.client else None
	return {
		"claim": claim,
		"policy": policy,
		"client": client,
		"documents": claim.get("claim_documents") or [],
		"fmt_money": fmt_money,
		"formatdate": formatdate,
		"_": _,
	}


@frappe.whitelist()
def get_print_html(doctype, name, template_key=None):
	"""Render a print template and return HTML string."""
	if not frappe.has_permission(doctype, "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	key = template_key or doctype
	template = TEMPLATE_MAP.get(key)
	if not template:
		frappe.throw(_("No print template configured for {0}").format(key))

	if doctype == "Insurance Policy" or key == "Insurance Policy":
		ctx = _policy_context(name)
	elif doctype == "Insurance Claim" or key in ("Insurance Claim", "claim_settlement"):
		ctx = _claim_context(name)
	else:
		frappe.throw(_("Unsupported doctype for print: {0}").format(doctype))

	html = frappe.render_template(template, ctx)
	return html


@frappe.whitelist()
def download_policy_schedule(policy):
	html = get_print_html("Insurance Policy", policy)
	frappe.local.response.filename = f"Policy-{policy}.html"
	frappe.local.response.filecontent = html
	frappe.local.response.type = "download"
