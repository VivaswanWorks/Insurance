import json
import os

import frappe


OLD_MODULE = "Insurance"
NEW_MODULE = "Insurance Core"
OLD_APP = "insurance"
NEW_APP = "insurance_core"


def execute():
	_ensure_new_module()
	_relabel_records("DocType", _json_names("doctype"))
	_relabel_records("Report", _json_names("report"))
	_relabel_owned_artefacts()
	_rename_workspace()
	_retire_old_module()


def _ensure_new_module():
	if not frappe.db.exists("Module Def", NEW_MODULE):
		frappe.get_doc({
			"doctype": "Module Def",
			"module_name": NEW_MODULE,
			"app_name": NEW_APP,
		}).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("Module Def", NEW_MODULE, "app_name", NEW_APP, update_modified=False)


def _old_module_is_ours():
	if not frappe.db.exists("Module Def", OLD_MODULE):
		return False
	app_name = frappe.db.get_value("Module Def", OLD_MODULE, "app_name")
	return app_name in (OLD_APP, NEW_APP, None, "")


def _json_names(kind):
	path = frappe.get_app_path(NEW_APP, "insurance_core", kind)
	if not os.path.isdir(path):
		return []
	names = []
	for folder in os.listdir(path):
		json_path = os.path.join(path, folder, f"{folder}.json")
		if not os.path.isfile(json_path):
			continue
		with open(json_path) as handle:
			data = json.load(handle)
		name = data.get("name")
		if name:
			names.append(name)
	return names


def _relabel_records(doctype, names):
	if not names or not frappe.db.table_exists(doctype):
		return
	if not frappe.db.has_column(doctype, "module"):
		return
	placeholders = ", ".join(["%s"] * len(names))
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}`
		SET module = %s
		WHERE module = %s AND name IN ({placeholders})
		""",
		tuple([NEW_MODULE, OLD_MODULE, *names]),
	)


def _relabel_owned_artefacts():
	if not _old_module_is_ours():
		return
	for dt in (
		"Print Format",
		"Notification",
		"Client Script",
		"Server Script",
		"Web Form",
		"Page",
		"Dashboard",
		"Dashboard Chart",
		"Number Card",
		"Custom Field",
		"Property Setter",
		"Workspace",
	):
		if not frappe.db.table_exists(dt) or not frappe.db.has_column(dt, "module"):
			continue
		frappe.db.sql(
			f"UPDATE `tab{dt}` SET module = %s WHERE module = %s",
			(NEW_MODULE, OLD_MODULE),
		)


def _rename_workspace():
	if frappe.db.exists("Workspace", OLD_MODULE) and _old_module_is_ours():
		if not frappe.db.exists("Workspace", NEW_MODULE):
			frappe.rename_doc("Workspace", OLD_MODULE, NEW_MODULE, force=True, ignore_permissions=True)
	if frappe.db.exists("Workspace", NEW_MODULE):
		frappe.db.set_value(
			"Workspace",
			NEW_MODULE,
			{"module": NEW_MODULE, "label": NEW_MODULE, "title": NEW_MODULE},
			update_modified=False,
		)


def _retire_old_module():
	if not _old_module_is_ours():
		return
	if frappe.db.count("DocType", {"module": OLD_MODULE}):
		return
	if frappe.db.exists("Module Def", OLD_MODULE) and frappe.db.exists("Module Def", NEW_MODULE):
		frappe.delete_doc("Module Def", OLD_MODULE, force=True, ignore_permissions=True)
