import json
import os

import frappe


ROLES = [
	"Insurance Manager",
	"Insurance Agent",
	"Claims Adjuster",
	"Compliance Officer",
	"Insurance User",
]


def after_install():
	ensure_roles()
	ensure_module()
	seed_eligibility_criteria()
	setup_ai_triage()


def after_migrate():
	ensure_roles()
	ensure_module()
	seed_eligibility_criteria()
	setup_ai_triage()


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			doc = frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1})
			doc.insert(ignore_permissions=True)


def ensure_module():
	if not frappe.db.exists("Module Def", "Insurance Core"):
		frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Insurance Core",
			"app_name": "insurance_core",
		}).insert(ignore_permissions=True)


def seed_eligibility_criteria():
	"""Seed system eligibility rules. Idempotent: skips existing criteria_code / criteria_name."""
	if not frappe.db.exists("DocType", "Client Eligibility Criteria"):
		return
	# Keep seed data outside fixtures/ so Frappe sync_fixtures does not force-import it
	path = frappe.get_app_path("insurance_core", "data", "client_eligibility_criteria.json")
	if not os.path.exists(path):
		# Backward-compatible fallback if site still has old layout
		path = frappe.get_app_path("insurance_core", "fixtures", "client_eligibility_criteria.json")
	if not os.path.exists(path):
		return
	with open(path) as handle:
		rows = json.load(handle)
	for row in rows:
		code = row.get("criteria_code")
		if not code:
			continue
		# Skip if already present under any name (naming-series or criteria_code)
		if frappe.db.exists("Client Eligibility Criteria", {"criteria_code": code}):
			continue
		criteria_name = row.get("criteria_name")
		if criteria_name and frappe.db.exists(
			"Client Eligibility Criteria", {"criteria_name": criteria_name}
		):
			continue
		# Prefer stable name = criteria_code for system rows
		row = dict(row)
		row.setdefault("name", code)
		row["doctype"] = "Client Eligibility Criteria"
		doc = frappe.get_doc(row)
		doc.insert(ignore_permissions=True)


def setup_ai_triage():
	"""Create Flow tools/agent/trigger and AI custom fields when Flow is available."""
	try:
		from insurance_core.ai_triage import ensure_flow_triage_setup

		ensure_flow_triage_setup()
	except Exception as e:
		# Non-fatal during migrate when Flow is not yet installed
		try:
			frappe.logger("insurance_core").warning(f"AI triage setup skipped: {e}")
		except Exception:
			pass
