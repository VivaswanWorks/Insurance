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


def after_migrate():
	ensure_roles()
	seed_eligibility_criteria()


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			doc = frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1})
			doc.insert(ignore_permissions=True)


def ensure_module():
	if not frappe.db.exists("Module Def", "Insurance"):
		frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Insurance",
			"app_name": "insurance",
		}).insert(ignore_permissions=True)


def seed_eligibility_criteria():
	if not frappe.db.exists("DocType", "Client Eligibility Criteria"):
		return
	path = frappe.get_app_path("insurance", "fixtures", "client_eligibility_criteria.json")
	if not os.path.exists(path):
		return
	with open(path) as handle:
		rows = json.load(handle)
	for row in rows:
		code = row.get("criteria_code")
		if not code:
			continue
		if frappe.db.exists("Client Eligibility Criteria", {"criteria_code": code}):
			continue
		doc = frappe.get_doc(row)
		doc.insert(ignore_permissions=True)
