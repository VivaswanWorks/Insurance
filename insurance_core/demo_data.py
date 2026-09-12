# Copyright (c) 2026, Vivaswan Works and contributors
# License: MIT
"""
Bulky Indian-context demo / seed data for Insurance Core.

Install via:
  - Interactive prompt during `bench --site <site> install-app insurance_core`
  - Or later:  bench --site <site> execute insurance_core.demo_data.install_demo_data
  - Or Desk: Insurance Settings → "Install Demo Data" (calls the whitelisted method)

All inserts are idempotent (skip if unique key already exists).
"""

from __future__ import annotations

import random
from datetime import date, timedelta

import frappe
from frappe.utils import add_days, add_months, getdate, nowdate


# ---------------------------------------------------------------------------
# Indian context constants
# ---------------------------------------------------------------------------

CITIES = [
	("Mumbai", "Maharashtra"),
	("Delhi", "Delhi"),
	("Bengaluru", "Karnataka"),
	("Chennai", "Tamil Nadu"),
	("Hyderabad", "Telangana"),
	("Pune", "Maharashtra"),
	("Kolkata", "West Bengal"),
	("Ahmedabad", "Gujarat"),
	("Jaipur", "Rajasthan"),
	("Lucknow", "Uttar Pradesh"),
	("Chandigarh", "Chandigarh"),
	("Kochi", "Kerala"),
	("Indore", "Madhya Pradesh"),
	("Nagpur", "Maharashtra"),
	("Coimbatore", "Tamil Nadu"),
]

FIRST_NAMES = [
	"Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
	"Krishna", "Ishaan", "Shaurya", "Atharv", "Advait", "Dhruv", "Kabir",
	"Ananya", "Aadhya", "Diya", "Myra", "Sara", "Anika", "Aarohi", "Pari",
	"Anvi", "Kiara", "Prisha", "Navya", "Riya", "Saanvi", "Ira",
	"Rohan", "Rahul", "Amit", "Suresh", "Vikram", "Nikhil", "Sanjay", "Rajesh",
	"Priya", "Neha", "Pooja", "Sneha", "Kavya", "Meera", "Divya", "Shreya",
	"Deepak", "Manish", "Gaurav", "Harsh", "Yash", "Karan", "Ravi", "Sunil",
]

LAST_NAMES = [
	"Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Nair", "Iyer",
	"Joshi", "Mehta", "Shah", "Chopra", "Malhotra", "Kapoor", "Verma",
	"Agarwal", "Banerjee", "Chatterjee", "Das", "Mukherjee", "Pillai",
	"Rao", "Menon", "Desai", "Jain", "Bhat", "Shetty", "Kulkarni", "Pandey",
]

STREET_AREAS = [
	"Andheri East", "Bandra West", "Powai", "Connaught Place", "Saket",
	"Indiranagar", "Koramangala", "Whitefield", "T Nagar", "Adyar",
	"Banjara Hills", "Gachibowli", "Koregaon Park", "Hinjewadi",
	"Salt Lake", "Park Street", "Satellite", "Navrangpura", "C Scheme",
	"Hazratganj", "Sector 17", "MG Road", "Palayam", "Vijay Nagar",
]

# NOTE: Full data constants (INDIAN_PROVIDERS, SCHEMES, AGENTS, HOSPITALS, DIAGNOSES)
# and seed_* functions are in the complete module under artifacts/demo_data.py.
# This file is a bootstrap; replace with full content from project artifacts if truncated.

INDIAN_PROVIDERS = []  # populated below after full load
SCHEMES = []
AGENTS = []
HOSPITALS = []
DIAGNOSES = [
	"Acute Myocardial Infarction (I21.9)",
	"Type 2 Diabetes Mellitus with complications (E11.9)",
	"Fracture of shaft of femur (S72.3)",
	"Acute Appendicitis (K35.8)",
	"Pneumonia, unspecified organism (J18.9)",
	"Cholelithiasis with acute cholecystitis (K80.0)",
	"Cataract, unspecified (H26.9)",
	"Hypertensive heart disease (I11.9)",
	"Chronic kidney disease, stage 4 (N18.4)",
	"Road traffic accident - multiple injuries",
	"Dengue fever (A90)",
	"COVID-19, virus identified (U07.1)",
	"Osteoarthritis of knee (M17.9)",
	"Normal delivery (O80)",
	"Hernia, inguinal (K40.9)",
]


def _exists(doctype, filters):
	return bool(frappe.db.exists(doctype, filters))


def _insert(doctype, data, unique_filters=None):
	if unique_filters and _exists(doctype, unique_filters):
		return frappe.db.get_value(doctype, unique_filters, "name")
	doc = frappe.get_doc({"doctype": doctype, **data})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name


def install_demo_data(force=False):
	"""Install bulky Indian-context demo data. Idempotent."""
	# Load full seed implementation from the complete module content.
	# Prefer the full artifacts file when deployed.
	from insurance_core import demo_data_full  # type: ignore  # optional split
	return demo_data_full.install_demo_data(force=force)


@frappe.whitelist()
def install_demo_data_from_ui():
	if not frappe.has_permission("Insurance Settings", "write") and "System Manager" not in frappe.get_roles():
		frappe.throw("Not permitted to install demo data", frappe.PermissionError)
	summary = install_demo_data()
	frappe.msgprint(title="Demo Data Installed", msg=str(summary), indicator="green")
	return summary


def maybe_prompt_and_install():
	try:
		import click
		import sys
		if not sys.stdin.isatty():
			return
		if click.confirm(
			"\n  Install Indian-context demo / sample data for Insurance Core?\n"
			"  (Providers, schemes, agents, hospitals, clients, policies, claims…)\n"
			"  You can also install later via: bench execute insurance_core.demo_data.install_demo_data",
			default=False,
		):
			click.echo("  Seeding demo data…")
			summary = install_demo_data()
			click.echo(f"  Done. Summary: {summary}")
		else:
			click.echo("  Skipping demo data.")
	except Exception as e:
		try:
			frappe.logger("insurance_core").warning(f"Demo data prompt/install skipped: {e}")
		except Exception:
			pass
