# Copyright (c) 2026, Vivaswan Works and contributors
# License: MIT. See license.txt

"""AI claim triage using Frappe Flow.

Provides:
- Flow-compatible tools that wrap the existing eligibility engine and claim context
- Orchestration that runs a Flow Agent and applies process / reject / pending actions
- Setup helpers that create the Flow Tool / Agent / Trigger records (idempotent)
"""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

# ---------------------------------------------------------------------------
# Thresholds (can later be moved to Insurance Settings)
# ---------------------------------------------------------------------------
HIGH_PROBABILITY = 80
LOW_PROBABILITY = 40
AGENT_TITLE = "Claim Triage Agent"
TRIGGER_TITLE = "Claim AI Triage on Submit/Update"


# ---------------------------------------------------------------------------
# Flow tools (imported via Flow Tool import_path)
# ---------------------------------------------------------------------------

def _eligibility_summary(claim_name: str) -> dict[str, Any]:
	"""Run deterministic eligibility and return a serialisable summary."""
	from insurance_core.eligibility import evaluate_claim_eligibility

	claim = frappe.get_doc("Insurance Claim", claim_name)
	result = evaluate_claim_eligibility(claim)

	criteria = []
	for row in result.criteria_results or []:
		criteria.append(
			{
				"criteria": row.get("eligibility_criteria") or row.get("criteria_code"),
				"result": row.get("result"),
				"is_mandatory": cint(row.get("is_mandatory")),
				"weightage": flt(row.get("weightage")),
				"score_contribution": flt(row.get("score_contribution")),
				"remarks": row.get("remarks") or "",
			}
		)

	return {
		"claim": claim_name,
		"overall_score": flt(result.overall_score),
		"overall_status": result.overall_status,
		"can_submit": bool(result.can_submit),
		"failed_mandatory": list(result.failed_mandatory or []),
		"warnings": list(result.warnings or []),
		"block_messages": list(result.block_messages or []),
		"criteria_results": criteria,
		"evaluation_name": result.evaluation_name,
	}


def get_claim_eligibility(claim_name: str) -> dict[str, Any]:
	"""Return the deterministic Claim Success Score and per-criteria results.

	Always call this first before making a triage recommendation.
	"""
	if not claim_name or not frappe.db.exists("Insurance Claim", claim_name):
		return {"error": f"Insurance Claim {claim_name!r} not found"}
	return _eligibility_summary(claim_name)


def get_claim_context(claim_name: str) -> dict[str, Any]:
	"""Return claim + linked policy / client / scheme / documents context for triage."""
	if not claim_name or not frappe.db.exists("Insurance Claim", claim_name):
		return {"error": f"Insurance Claim {claim_name!r} not found"}

	claim = frappe.get_doc("Insurance Claim", claim_name)
	policy = None
	client = None
	scheme = None

	if claim.policy and frappe.db.exists("Insurance Policy", claim.policy):
		policy = frappe.get_doc("Insurance Policy", claim.policy)
	if claim.client and frappe.db.exists("Insurance Client", claim.client):
		client = frappe.get_doc("Insurance Client", claim.client)
	scheme_name = claim.scheme or (policy.scheme if policy else None)
	if scheme_name and frappe.db.exists("Insurance Scheme", scheme_name):
		scheme = frappe.get_doc("Insurance Scheme", scheme_name)

	docs = []
	for d in claim.get("claim_documents") or []:
		docs.append(
			{
				"document_type": d.get("document_type"),
				"has_attachment": bool(d.get("attachment")),
				"verified": cint(d.get("verified")),
			}
		)

	members = []
	if policy:
		for m in policy.get("policy_members") or []:
			members.append({"member_name": m.get("member_name"), "relation": m.get("relation")})

	return {
		"claim": {
			"name": claim.name,
			"claim_number": claim.claim_number,
			"status": claim.status,
			"claim_type": claim.claim_type,
			"incident_date": str(claim.incident_date) if claim.incident_date else None,
			"reported_date": str(claim.reported_date) if claim.reported_date else None,
			"submission_date": str(claim.submission_date) if claim.submission_date else None,
			"claimed_amount": flt(claim.claimed_amount),
			"approved_amount": flt(claim.approved_amount),
			"description": (claim.description or "")[:2000],
			"diagnosis": claim.diagnosis,
			"treatment_details": (claim.treatment_details or "")[:1500],
			"hospital": claim.hospital,
			"claimant": claim.claimant,
			"eligibility_score": flt(claim.eligibility_score),
			"eligibility_status": claim.eligibility_status,
		},
		"policy": {
			"name": policy.name if policy else None,
			"status": policy.status if policy else None,
			"start_date": str(policy.start_date) if policy and policy.start_date else None,
			"end_date": str(policy.end_date) if policy and policy.end_date else None,
			"sum_assured": flt(policy.sum_assured) if policy else None,
			"payment_status": getattr(policy, "payment_status", None) if policy else None,
			"members": members,
		}
		if policy
		else None,
		"client": {
			"name": client.name if client else None,
			"lifecycle_stage": getattr(client, "lifecycle_stage", None) if client else None,
		}
		if client
		else None,
		"scheme": {
			"name": scheme.name if scheme else None,
			"line_of_business": getattr(scheme, "line_of_business", None) if scheme else None,
			"waiting_period_days": cint(getattr(scheme, "waiting_period_days", 0)) if scheme else 0,
		}
		if scheme
		else None,
		"documents": docs,
	}


def apply_triage_decision(
	claim_name: str,
	success_probability: float,
	recommended_action: str,
	reasons: str,
	missing_items: str = "",
	suggested_improvements: str = "",
	apply_status_change: int = 1,
) -> dict[str, Any]:
	"""Apply a triage decision to an Insurance Claim.

	recommended_action must be one of: process | reject | pending
	- process  → Under Review (high probability)
	- reject   → Rejected + rejection_reason
	- pending  → Additional Info Required + suggestion notes

	Writes assessment_notes, optional suggestion document, and AI fields.
	Does NOT settle or approve payouts — human still owns final authority.
	"""
	action = (recommended_action or "").strip().lower()
	if action not in ("process", "reject", "pending"):
		return {"error": f"Invalid recommended_action {recommended_action!r}. Use process|reject|pending."}

	if not claim_name or not frappe.db.exists("Insurance Claim", claim_name):
		return {"error": f"Insurance Claim {claim_name!r} not found"}

	claim = frappe.get_doc("Insurance Claim", claim_name)
	prob = flt(success_probability)
	now = now_datetime()

	_ensure_ai_fields()
	claim.db_set("ai_success_probability", prob, update_modified=False)
	claim.db_set("ai_recommended_action", action, update_modified=False)
	claim.db_set("ai_triage_at", now, update_modified=False)

	notes_parts = [
		f"[AI Triage {now}]",
		f"Success probability: {prob:.0f}%",
		f"Recommended action: {action}",
		f"Reasons: {reasons or '—'}",
	]
	if missing_items:
		notes_parts.append(f"Missing / incomplete: {missing_items}")
	if suggested_improvements:
		notes_parts.append(f"Suggestions: {suggested_improvements}")

	triage_block = "\n".join(notes_parts)
	existing_notes = (claim.assessment_notes or "").strip()
	new_notes = f"{existing_notes}\n\n{triage_block}".strip() if existing_notes else triage_block
	claim.db_set("assessment_notes", new_notes, update_modified=False)

	suggestion_name = None
	if action == "pending" and (missing_items or suggested_improvements):
		suggestion_name = _create_suggestion_document(
			claim, missing_items=missing_items, suggested_improvements=suggested_improvements, reasons=reasons
		)
		if suggestion_name:
			claim.db_set("ai_suggestion_document", suggestion_name, update_modified=False)

	status_changed = None
	if cint(apply_status_change):
		allowed_from = {
			"Draft",
			"Submitted",
			"Under Review",
			"Documents Pending",
			"Additional Info Required",
		}
		if claim.status in allowed_from:
			if action == "process":
				new_status = "Under Review"
			elif action == "reject":
				new_status = "Rejected"
				if reasons:
					claim.db_set("rejection_reason", (reasons or "")[:140], update_modified=False)
					claim.db_set("decision", "Reject", update_modified=False)
			else:
				new_status = "Additional Info Required"

			if new_status != claim.status:
				claim.db_set("status", new_status, update_modified=True)
				status_changed = new_status
				_log_assessment(claim.name, f"AI triage → {new_status}", triage_block)

	return {
		"claim": claim_name,
		"success_probability": prob,
		"recommended_action": action,
		"status_changed_to": status_changed,
		"suggestion_document": suggestion_name,
		"message": _("Triage applied: {0} ({1}%)").format(action, int(prob)),
	}


# See full module in artifacts/ai_triage.py for orchestration, setup, and helpers.
# PLACEHOLDER_CONTINUE
