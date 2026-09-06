app_name = "insurance"
app_title = "Insurance"
app_publisher = "Aegis"
app_description = "Insurance ERP on Frappe — providers, schemes, policies, claims, compliance"
app_email = "hello@aegis.local"
app_license = "mit"
app_version = "0.0.1"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "insurance",
		"logo": "/assets/insurance/images/insurance.svg",
		"title": "Insurance",
		"route": "/insurance",
		"has_permission": "insurance.api.check_app_permission",
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
	{"from_route": "/insurance/<path:app_path>", "to_route": "insurance"},
]

app_include_js = []
app_include_css = []

after_install = "insurance.install.after_install"
after_migrate = "insurance.install.after_migrate"

scheduler_events = {
	"daily": [
		"insurance.tasks.send_renewal_reminders",
		"insurance.tasks.send_premium_reminders",
		"insurance.tasks.expire_policies",
		"insurance.tasks.mark_overdue_compliance",
		"insurance.tasks.lapse_grace_policies",
	],
	"hourly": [
		"insurance.tasks.flush_queued_communications",
	],
}

doc_events = {
	"Insurance Policy": {
		"on_update": "insurance.integrations.sync_policy_to_erpnext",
	},
	"Insurance Client": {
		"after_insert": "insurance.integrations.sync_client_from_crm",
		"on_update": "insurance.integrations.sync_client_to_erpnext",
	},
	"Insurance Claim": {
		"on_update": "insurance.integrations.sync_claim_ticket",
	},
}

override_doctype_class = {}

user_privacy_documents = [
	{"doctype": "Insurance Client", "match_field": "email"},
]

export_python_type_annotations = True

website_redirects = []
