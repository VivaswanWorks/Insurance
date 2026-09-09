"""TPA / cashless authorization helpers.

- Resolve TPA from hospital or provider
- Validate network hospital for cashless claims
- Create and transition Cashless Authorization documents
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, nowdate


def resolve_tpa(claim_or_hospital=None, provider=None, hospital=None) -> str | None:
	"""Pick TPA (Insurance Provider with type TPA) for routing."""
	hospital = hospital or (claim_or_hospital.get("hospital") if hasattr(claim_or_hospital, "get") else None)
	provider = provider or (claim_or_hospital.get("provider") if hasattr(claim_or_hospital, "get") else None)

	if hospital and frappe.db.exists("Network Hospital", hospital):
		tpa = frappe.db.get_value("Network Hospital", hospital, "tpa")
		if tpa:
			return tpa
		prov = frappe.db.get_value("Network Hospital", hospital, "provider")
		if prov:
			ptype = frappe.db.get_value("Insurance Provider", prov, "provider_type")
			if ptype == "TPA":
				return prov

	if provider:
		ptype = frappe.db.get_value("Insurance Provider", provider, "provider_type")
		if ptype == "TPA":
			return provider
		# optional linked TPA field if present on provider in future
		if frappe.db.has_column("Insurance Provider", "default_tpa"):
			return frappe.db.get_value("Insurance Provider", provider, "default_tpa")
	return None


def validate_cashless_hospital(hospital, throw=True) -> bool:
	if not hospital:
		if throw:
			frappe.throw(_("Cashless claims require a network hospital."), title=_("Hospital Required"))
		return False
	row = frappe.db.get_value(
		"Network Hospital",
		hospital,
		["status", "cashless", "hospital_name"],
		as_dict=True,
	)
	if not row:
		if throw:
			frappe.throw(_("Selected hospital is not in the network."), title=_("Invalid Hospital"))
		return False
	if row.status != "Active":
		if throw:
			frappe.throw(
				_("{0} is not an active network hospital.").format(row.hospital_name),
				title=_("Inactive Hospital"),
			)
		return False
	if not cint_bool(row.cashless):
		if throw:
			frappe.throw(
				_("{0} is not enabled for cashless treatment.").format(row.hospital_name),
				title=_("Cashless Not Enabled"),
			)
		return False
	return True


def cint_bool(v):
	from frappe.utils import cint

	return bool(cint(v))


def ensure_cashless_authorization(claim, requested_amount=None):
	"""Create a Cashless Authorization for a cashless claim if missing."""
	if isinstance(claim, str):
		claim = frappe.get_doc("Insurance Claim", claim)

if (claim.claim_type or "") != "Cashless":
		return None
	if not frappe.db.exists("DocType", "Cashless Authorization"):
		return None

	existing = frappe.db.get_value("Cashless Authorization", {"claim": claim.name}, "name")
	if existing:
		return existing

	validate_cashless_hospital(claim.hospital, throw=True)
	tpa = resolve_tpa(claim)
	doc = frappe.get_doc(
		{
			"doctype": "Cashless Authorization",
			"claim": claim.name,
			"policy": claim.policy,
			"client": claim.client,
			"hospital": claim.hospital,
			"tpa": tpa,
			"provider": claim.provider,
			"requested_amount": flt(requested_amount or claim.claimed_amount),
			"status": "Requested",
			"request_date": nowdate(),
			"admission_date": claim.admission_date,
			"diagnosis": claim.diagnosis,
		}
	)
	doc.insert(ignore_permissions=True)

	if claim.meta.has_field("tpa") and tpa:
		frappe.db.set_value("Insurance Claim", claim.name, "tpa", tpa, update_modified=False)
	if claim.meta.has_field("cashless_authorization"):
		frappe.db.set_value(
			"Insurance Claim", claim.name, "cashless_authorization", doc.name, update_modified=False
		)
	return doc.name


@frappe.whitelist()
def request_cashless_authorization(claim, requested_amount=None):
	name = ensure_cashless_authorization(claim, requested_amount=requested_amount)
	if not name:
		frappe.throw(_("Cashless authorization is only for Cashless claims."), title=_("Not Cashless"))
	return name


@frappe.whitelist()
def approve_cashless_authorization(name, approved_amount=None, authorization_code=None):
	doc = frappe.get_doc("Cashless Authorization", name)
	if doc.status not in ("Requested", "Under Review", "Query Raised"):
		frappe.throw(_("Cannot approve from status {0}.").format(doc.status), title=_("Invalid Status"))
	if "Insurance Manager" not in frappe.get_roles() and "Claims Adjuster" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted to approve cashless authorization."), frappe.PermissionError)
	doc.status = "Approved"
	doc.approved_amount = flt(approved_amount if approved_amount is not None else doc.requested_amount)
	doc.authorization_code = authorization_code or doc.authorization_code or frappe.generate_hash(length=10).upper()
	doc.decision_date = nowdate()
	doc.decided_by = frappe.session.user
	doc.save()
	_sync_claim_from_auth(doc)
	return doc.name


@frappe.whitelist()
def reject_cashless_authorization(name, reason=None):
	doc = frappe.get_doc("Cashless Authorization", name)
	if doc.status in ("Approved", "Rejected", "Cancelled", "Utilized"):
		frappe.throw(_("Cannot reject from status {0}.").format(doc.status))
	doc.status = "Rejected"
	doc.decision_date = nowdate()
	doc.decided_by = frappe.session.user
	if reason:
		doc.remarks = (doc.remarks or "") + f"\nRejection: {reason}"
	doc.save()
	return doc.name


@frappe.whitelist()
def mark_cashless_utilized(name, utilized_amount=None):
	doc = frappe.get_doc("Cashless Authorization", name)
	if doc.status != "Approved":
		frappe.throw(_("Only Approved authorizations can be marked Utilized."))
	doc.status = "Utilized"
	doc.utilized_amount = flt(utilized_amount if utilized_amount is not None else doc.approved_amount)
	doc.utilized_on = nowdate()
	doc.save()
	_sync_claim_from_auth(doc)
	return doc.name


def _sync_claim_from_auth(auth):
	if not auth.claim or not frappe.db.exists("Insurance Claim", auth.claim):
		return
	updates = {}
	claim_meta = frappe.get_meta("Insurance Claim")
	if auth.status == "Approved":
		if claim_meta.has_field("approved_amount") and flt(auth.approved_amount):
			updates["approved_amount"] = auth.approved_amount
		if claim_meta.has_field("cashless_auth_code"):
			updates["cashless_auth_code"] = auth.authorization_code
		# move claim into under review if still submitted
		status = frappe.db.get_value("Insurance Claim", auth.claim, "status")
		if status in ("Draft", "Submitted"):
			updates["status"] = "Under Review"
	if updates:
		frappe.db.set_value("Insurance Claim", auth.claim, updates, update_modified=True)


@frappe.whitelist()
def get_network_hospitals(city=None, tpa=None, cashless_only=1):
	filters = {"status": "Active"}
	if city:
		filters["city"] = city
	if tpa:
		filters["tpa"] = tpa
	if cint_bool(cashless_only):
		filters["cashless"] = 1
	return frappe.get_all(
		"Network Hospital",
		filters=filters,
		fields=["name", "hospital_name", "city", "tpa", "provider", "cashless", "phone"],
		order_by="hospital_name asc",
		limit_page_length=100,
	)
