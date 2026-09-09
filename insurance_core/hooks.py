app_name = "insurance_core"
app_title = "Insurance Core"
app_publisher = "Vivaswan Works"
app_description = "Core Insurance Management for Frappe / ERPNext"
app_email = "hello@vivaswan.in"
app_license = "mit"
app_version = "0.0.1"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "insurance_core",
		"logo": "/assets/insurance_core/images/insurance.svg",
		"title": "Insurance Core",
		"route": "/insurance_core",
		"has_permission": "insurance_core.api.check_app_permission",
	}
]

fixtures = [
	{"dt": "Role", "filters": [["name", "in", [
		"Insurance Manager",
		"Insurance Agent",
		"Claims Adjuster",
		"Compliance Officer",
		"Insurance User",
	]]]},
]

website_route_rules = [
	{"from_route": "/insurance_core/<path:app_path>", "to_route": "insurance_core"},
]

app_include_js = []
app_include_css = []

after_install = "insurance_core.install.after_install"
after_migrate = "insurance_core.install.after_migrate"

scheduler_events = {
	"daily": [
		"insurance_core.tasks.send_renewal_reminders",
		"insurance_core.tasks.send_premium_reminders",
		"insurance_core.tasks.expire_policies",
		"insurance_core.tasks.mark_overdue_compliance",
		"insurance_core.tasks.lapse_grace_policies",
		"insurance_core.tasks.rescore_open_claims",
	],
	"hourly": [
		"insurance_core.tasks.flush_queued_communications",
	],
}

doc_events = {
	"Insurance Policy": {
		"on_update": "insurance_core.integrations.sync_policy_to_erpnext",
	},
	"Insurance Client": {
		"after_insert": "insurance_core.integrations.sync_client_from_crm",
		"on_update": "insurance_core.integrations.sync_client_to_erpnext",
	},
	"Insurance Claim": {
		"on_update": "insurance_core.integrations.sync_claim_ticket",
	},
}

override_doctype_class = {}

user_privacy_documents = [
	{"doctype": "Insurance Client", "match_field": "email"},
]

export_python_type_annotations = True

website_redirects = []
