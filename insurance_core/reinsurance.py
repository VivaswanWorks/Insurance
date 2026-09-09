"""Reinsurance helpers: treaty resolution, cession amounts, claim recovery.

Supports Facultative and Treaty cessions stored on Insurance Policy.
On claim settlement, computes reinsurer share and creates Claim Recovery.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, nowdate


def get_policy_cession(policy) -> dict:
	"""Return cession metadata for a policy."""
	if isinstance(policy, str):
		policy = frappe.get_doc("Insurance Policy", policy)

	rtype = (policy.get("reinsurance_type") or "").strip()
	pct = flt(policy.get("cession_percentage"))
	treaty = policy.get("reinsurance_treaty")
	reinsurer = policy.get("reinsurer")

	if treaty and frappe.db.exists("DocType", "Reinsurance Treaty"):
		row = frappe.db.get_value(
			"Reinsurance Treaty",
			treaty,
			["name", "treaty_type", "cession_percentage", "reinsurer", "status", "retention_limit"],
			as_dict=True,
		)
		if row and row.status == "Active":
			rtype = rtype or row.treaty_type
			if not pct:
				pct = flt(row.cession_percentage)
			reinsurer = reinsurer or row.reinsurer

	return {
		"reinsurance_type": rtype or None,
		"cession_percentage": pct,
		"treaty": treaty,
		"reinsurer": reinsurer,
		"active": bool(rtype and pct > 0),
	}


def calculate_cession_amount(gross_amount, cession_percentage) -> float:
	return flt(flt(gross_amount) * flt(cession_percentage) / 100.0, 2)


def calculate_claim_cession(claim) -> dict:
	"""Cession share of a settled / approved claim amount."""
	if isinstance(claim, str):
		claim = frappe.get_doc("Insurance Claim", claim)
	if not claim.policy:
		return {"cession_amount": 0.0, "cession_percentage": 0.0, "active": False}

	meta = get_policy_cession(claim.policy)
	if not meta["active"]:
		return {"cession_amount": 0.0, "cession_percentage": 0.0, "active": False, **meta}

	base = flt(claim.settled_amount or claim.approved_amount or claim.claimed_amount)
	amount = calculate_cession_amount(base, meta["cession_percentage"])
	return {
		**meta,
		"gross_amount": base,
		"cession_amount": amount,
		"retention_amount": flt(base - amount, 2),
	}


def ensure_reinsurance_recovery(claim, force=False):
	"""Create or update a Claim Recovery of type Reinsurance for the claim."""
	if isinstance(claim, str):
		claim_name = claim
		claim = frappe.get_doc("Insurance Claim", claim)
	else:
		claim_name = claim.name

	breakdown = calculate_claim_cession(claim)
	if not breakdown.get("active") or flt(breakdown.get("cession_amount")) <= 0:
		return None

	if not frappe.db.exists("DocType", "Claim Recovery"):
		return None

	existing = frappe.db.get_value(
		"Claim Recovery",
		{"claim": claim_name, "recovery_type": "Reinsurance"},
		"name",
	)
	if existing and not force:
		# refresh amount if still Open
		status = frappe.db.get_value("Claim Recovery", existing, "status")
		if status in ("Open", "In Progress"):
			frappe.db.set_value(
				"Claim Recovery",
				existing,
				{
					"amount": breakdown["cession_amount"],
					"party": breakdown.get("reinsurer") or "",
				},
				update_modified=False,
			)
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Claim Recovery",
			"claim": claim_name,
			"recovery_type": "Reinsurance",
			"amount": breakdown["cession_amount"],
			"status": "Open",
			"party": breakdown.get("reinsurer") or breakdown.get("treaty") or "Reinsurer",
			"notes": _(
				"Auto-created: {0}% cession on gross {1} ({2})"
			).format(
				breakdown["cession_percentage"],
				breakdown.get("gross_amount"),
				breakdown.get("reinsurance_type") or "",
			),
		}
	)
	doc.insert(ignore_permissions=True)

	# stamp claim field when present
	if claim.meta.has_field("reinsurance_recovery"):
		frappe.db.set_value(
			"Insurance Claim",
			claim_name,
			"reinsurance_recovery",
			breakdown["cession_amount"],
			update_modified=False,
		)
	return doc.name


def apply_treaty_defaults(policy_doc):
	"""When a treaty is selected on policy, copy type / % / reinsurer if empty."""
	if not policy_doc.get("reinsurance_treaty"):
		return
	if not frappe.db.exists("DocType", "Reinsurance Treaty"):
		return
	row = frappe.db.get_value(
		"Reinsurance Treaty",
		policy_doc.reinsurance_treaty,
		["treaty_type", "cession_percentage", "reinsurer", "status"],
		as_dict=True,
	)
	if not row or row.status != "Active":
		return
	if not policy_doc.reinsurance_type:
		policy_doc.reinsurance_type = row.treaty_type
	if not flt(policy_doc.cession_percentage):
		policy_doc.cession_percentage = flt(row.cession_percentage)
	if not policy_doc.get("reinsurer") and row.reinsurer:
		policy_doc.reinsurer = row.reinsurer


@frappe.whitelist()
def preview_claim_cession(claim):
	return calculate_claim_cession(claim)


@frappe.whitelist()
def create_reinsurance_recovery(claim):
	name = ensure_reinsurance_recovery(claim, force=False)
	if not name:
		frappe.throw(_("No active reinsurance cession on this claim's policy."), title=_("No Cession"))
	return name
