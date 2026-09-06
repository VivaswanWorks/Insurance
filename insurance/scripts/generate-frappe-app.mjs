import fs from 'fs'
import path from 'path'
import { fileURLToPath, pathToFileURL } from 'url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const { DOCTYPES } = await import(pathToFileURL(path.join(root, 'src/frappe/doctypes.js')).href)

const ROLE_PERMS = {
  'Insurance Manager': { '*': { read: 1, write: 1, create: 1, delete: 1, report: 1, export: 1, share: 1 } },
  'Insurance Agent': {
    'Insurance Provider': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 },
    'Insurance Scheme': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 },
    'Insurance Policy': { read: 1, write: 1, create: 1, delete: 0, report: 1, export: 1 },
    'Insurance Claim': { read: 1, write: 1, create: 1, delete: 0, report: 1, export: 0 },
    'Insurance Client': { read: 1, write: 1, create: 1, delete: 0, report: 1, export: 0 },
    'Compliance Record': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Insurance Communication': { read: 1, write: 1, create: 1, delete: 0, report: 0, export: 0 },
  },
  'Claims Adjuster': {
    'Insurance Provider': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Insurance Scheme': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Insurance Policy': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 },
    'Insurance Claim': { read: 1, write: 1, create: 1, delete: 0, report: 1, export: 1 },
    'Insurance Client': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Compliance Record': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Insurance Communication': { read: 1, write: 1, create: 1, delete: 0, report: 0, export: 0 },
  },
  'Compliance Officer': {
    'Insurance Provider': { read: 1, write: 1, create: 0, delete: 0, report: 1, export: 1 },
    'Insurance Scheme': { read: 1, write: 1, create: 0, delete: 0, report: 1, export: 1 },
    'Insurance Policy': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 },
    'Insurance Claim': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 },
    'Insurance Client': { read: 1, write: 0, create: 0, delete: 0, report: 0, export: 0 },
    'Compliance Record': { read: 1, write: 1, create: 1, delete: 0, report: 1, export: 1 },
    'Insurance Communication': { read: 1, write: 1, create: 1, delete: 0, report: 0, export: 0 },
  },
  'Insurance User': { '*': { read: 1, write: 0, create: 0, delete: 0, report: 1, export: 0 } },
}

function snake(name) {
  return name.replace(/[/]+/g, ' ').trim().replace(/\s+/g, '_').toLowerCase()
}

function className(name) {
  return name.replace(/[^A-Za-z0-9]+/g, ' ').trim().split(' ').map((w) => w[0].toUpperCase() + w.slice(1)).join('')
}

function selectOptions(options) {
  if (Array.isArray(options)) return options.join('\n')
  return options || ''
}

function permsFor(doctype) {
  const out = []
  for (const [role, table] of Object.entries(ROLE_PERMS)) {
    const spec = table[doctype] || table['*']
    if (!spec || !spec.read) continue
    out.push({
      role,
      read: spec.read || 0,
      write: spec.write || 0,
      create: spec.create || 0,
      delete: spec.delete || 0,
      submit: 0,
      cancel: 0,
      amend: 0,
      report: spec.report || 0,
      export: spec.export || 0,
      import: spec.create ? 1 : 0,
      share: spec.share || 0,
      print: spec.read || 0,
      email: spec.read || 0,
    })
  }
  return out
}

function toFrappeJson(meta) {
  const listMap = Object.fromEntries((meta.listView || []).map((c, i) => [c.fieldname, { ...c, idx: i }]))
  const fields = meta.fields.map((f, i) => {
    const row = {
      fieldname: f.fieldname,
      fieldtype: f.fieldtype,
      label: f.label || undefined,
      reqd: f.reqd || 0,
      unique: f.unique || 0,
      in_list_view: listMap[f.fieldname] ? 1 : 0,
      in_standard_filter: ['Select', 'Link'].includes(f.fieldtype) ? 1 : 0,
      in_global_search: (meta.search_fields || []).includes(f.fieldname) ? 1 : 0,
      bold: i === 0 ? 1 : 0,
      default: f.default,
      options:
        f.fieldtype === 'Select'
          ? selectOptions(f.options)
          : f.options || undefined,
      width: listMap[f.fieldname]?.width,
    }
    Object.keys(row).forEach((k) => {
      if (row[k] === undefined || row[k] === 0 || row[k] === '') delete row[k]
    })
    if (f.reqd) row.reqd = 1
    if (f.unique) row.unique = 1
    if (listMap[f.fieldname]) row.in_list_view = 1
    return row
  })

  let naming_rule = 'Random'
  if (meta.autoname?.startsWith('field:')) naming_rule = 'By fieldname'
  else if (meta.autoname) naming_rule = 'By "Naming Series" field'

  return {
    actions: [],
    allow_import: 1,
    allow_rename: 1,
    autoname: meta.autoname,
    creation: '2026-09-04 06:00:00',
    default_view: 'List',
    doctype: 'DocType',
    document_type: 'Document',
    engine: 'InnoDB',
    field_order: meta.fields.map((f) => f.fieldname),
    fields,
    index_web_pages_for_search: 1,
    is_submittable: 0,
    links: [],
    modified: '2026-09-04 06:00:00',
    modified_by: 'Administrator',
    module: 'Insurance',
    name: meta.name,
    naming_rule,
    owner: 'Administrator',
    permissions: permsFor(meta.name),
    search_fields: (meta.search_fields || []).join(', '),
    show_name_in_global_search: 1,
    sort_field: 'modified',
    sort_order: 'DESC',
    states: [],
    title_field: meta.title_field,
    track_changes: 1,
    track_seen: 1,
    track_views: 1,
  }
}

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, content.endsWith('\n') ? content : content + '\n')
}

const APP = path.join(root, 'insurance')
const PKG = path.join(APP, 'insurance')
const MOD = path.join(PKG, 'insurance')

const doctypes = { ...DOCTYPES }
if (doctypes.Communication) {
  const comm = JSON.parse(JSON.stringify(doctypes.Communication))
  comm.name = 'Insurance Communication'
  delete doctypes.Communication
  doctypes['Insurance Communication'] = comm
}

for (const [name, meta] of Object.entries(doctypes)) {
  meta.name = name
  const folder = snake(name)
  const dir = path.join(MOD, 'doctype', folder)
  const json = toFrappeJson(meta)
  write(path.join(dir, `${folder}.json`), JSON.stringify(json, null, 1))
  write(
    path.join(dir, `${folder}.py`),
    `import frappe
from frappe.model.document import Document


class ${className(name)}(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		pass

	def on_update(self):
		if hasattr(self, "sync_linked_apps"):
			self.sync_linked_apps()
`
  )
  write(
    path.join(dir, `${folder}.js`),
    `frappe.ui.form.on('${name}', {
	refresh(frm) {
		frm.trigger('show_integration_links');
	},
	show_integration_links(frm) {
		if (frm.doc.crm_lead) {
			frm.add_custom_button(__('Open CRM Lead'), () => {
				frappe.set_route('Form', 'CRM Lead', frm.doc.crm_lead);
			}, __('Frappe Apps'));
		}
		if (frm.doc.erpnext_customer) {
			frm.add_custom_button(__('Open Customer'), () => {
				frappe.set_route('Form', 'Customer', frm.doc.erpnext_customer);
			}, __('Frappe Apps'));
		}
		if (frm.doc.helpdesk_ticket) {
			frm.add_custom_button(__('Open Ticket'), () => {
				frappe.set_route('Form', 'HD Ticket', frm.doc.helpdesk_ticket);
			}, __('Frappe Apps'));
		}
	}
});
`
  )
  write(
    path.join(dir, `test_${folder}.py`),
    `import frappe
from frappe.tests.utils import FrappeTestCase


class Test${className(name)}(FrappeTestCase):
	def test_doctype_exists(self):
		self.assertTrue(frappe.db.exists("DocType", "${name}"))
`
  )
  write(path.join(dir, '__init__.py'), '')
}

write(path.join(MOD, 'doctype', '__init__.py'), '')
write(path.join(MOD, '__init__.py'), '')
write(path.join(PKG, '__init__.py'), '__version__ = "0.0.1"\n')
write(path.join(APP, '__init__.py'), '')

write(
  path.join(PKG, 'hooks.py'),
  `app_name = "insurance"
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
	{"dt": "Role Profile", "filters": [["name", "in", ["Insurance Desk"]]]},
	{"dt": "Custom Field", "filters": [["module", "=", "Insurance"]]},
]

website_route_rules = [
	{"from_route": "/insurance/<path:app_path>", "to_route": "insurance"},
	{"from_route": "/frontend/<path:app_path>", "to_route": "insurance"},
]

app_include_js = []
app_include_css = []

after_install = "insurance.install.after_install"
after_migrate = "insurance.install.after_migrate"

scheduler_events = {
	"daily": [
		"insurance.tasks.send_renewal_reminders",
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
`
)

write(path.join(PKG, 'modules.txt'), 'Insurance\n')
write(path.join(PKG, 'patches.txt'), '[pre_model_sync]\n\n[post_model_sync]\n')

write(
  path.join(PKG, 'install.py'),
  `import frappe


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


def after_migrate():
	ensure_roles()


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
`
)

write(
  path.join(PKG, 'api.py'),
  `import frappe


@frappe.whitelist()
def check_app_permission():
	return bool(set(frappe.get_roles()) & {
		"System Manager",
		"Insurance Manager",
		"Insurance Agent",
		"Claims Adjuster",
		"Compliance Officer",
		"Insurance User",
	})


@frappe.whitelist()
def ping():
	return {"ok": True, "user": frappe.session.user, "roles": frappe.get_roles()}
`
)

write(
  path.join(PKG, 'tasks.py'),
  `import frappe
from frappe.utils import add_days, nowdate, now_datetime


def send_renewal_reminders():
	cutoff = add_days(nowdate(), 30)
	policies = frappe.get_all(
		"Insurance Policy",
		filters={"status": ["in", ["Active", "Grace Period"]], "renewal_date": ["<=", cutoff]},
		fields=["name", "client", "renewal_date", "agent", "policy_number"],
	)
	for p in policies:
		exists = frappe.db.exists(
			"Insurance Communication",
			{"related_doctype": "Insurance Policy", "related_name": p.name, "template": "Renewal Reminder", "status": ["in", ["Queued", "Draft", "Sent"]]},
		)
		if exists:
			continue
		client_email = frappe.db.get_value("Insurance Client", p.client, "email")
		doc = frappe.get_doc({
			"doctype": "Insurance Communication",
			"subject": f"Renewal reminder — {p.policy_number}",
			"channel": "Email",
			"template": "Renewal Reminder",
			"recipient": client_email or p.client,
			"related_doctype": "Insurance Policy",
			"related_name": p.name,
			"scheduled_at": now_datetime(),
			"status": "Queued",
			"agent": p.agent,
			"body": f"Policy {p.policy_number} renews on {p.renewal_date}.",
		})
		doc.insert(ignore_permissions=True)


def mark_overdue_compliance():
	frappe.db.sql(
		"""
		update \`tabCompliance Record\`
		set status = 'Overdue'
		where due_date < %s and status not in ('Closed', 'Approved', 'Overdue')
		""",
		(nowdate(),),
	)


def lapse_grace_policies():
	frappe.db.sql(
		"""
		update \`tabInsurance Policy\`
		set status = 'Lapsed'
		where status = 'Grace Period' and renewal_date < %s
		""",
		(add_days(nowdate(), -15),),
	)


def flush_queued_communications():
	queued = frappe.get_all(
		"Insurance Communication",
		filters={"status": "Queued", "scheduled_at": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in queued:
		frappe.db.set_value("Insurance Communication", name, "status", "Sent")
`
)

write(
  path.join(PKG, 'integrations.py'),
  `import frappe


def _app_installed(app):
	return app in frappe.get_installed_apps()


def sync_client_from_crm(doc, method=None):
	if not doc.crm_lead or not _app_installed("crm"):
		return
	try:
		lead = frappe.get_doc("CRM Lead", doc.crm_lead)
		if not doc.email and getattr(lead, "email", None):
			doc.db_set("email", lead.email, update_modified=False)
	except frappe.DoesNotExistError:
		pass


def sync_client_to_erpnext(doc, method=None):
	if not _app_installed("erpnext"):
		return
	if doc.erpnext_customer and frappe.db.exists("Customer", doc.erpnext_customer):
		return
	if not frappe.db.exists("DocType", "Customer"):
		return
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": doc.full_name,
		"customer_type": "Company" if doc.client_type == "Corporate" else "Individual",
		"email_id": doc.email,
		"mobile_no": doc.phone,
	})
	customer.insert(ignore_permissions=True)
	doc.db_set("erpnext_customer", customer.name, update_modified=False)


def sync_policy_to_erpnext(doc, method=None):
	if not _app_installed("erpnext"):
		return
	if not frappe.db.exists("DocType", "Sales Invoice"):
		return


def sync_claim_ticket(doc, method=None):
	if not _app_installed("helpdesk"):
		return
	if doc.status in ("Submitted", "Documents Pending") and frappe.db.exists("DocType", "HD Ticket"):
		existing = frappe.db.exists("HD Ticket", {"subject": ["like", f"%{doc.claim_number}%"]})
		if existing:
			return
`
)

write(
  path.join(PKG, 'config', 'desktop.py'),
  `from frappe import _


def get_data():
	return [
		{
			"module_name": "Insurance",
			"type": "module",
			"label": _("Insurance"),
		}
	]
`
)
write(path.join(PKG, 'config', 'docs.py'), 'source_link = "https://github.com/aegis/insurance"\n')
write(path.join(PKG, 'config', '__init__.py'), '')

const reports = [
  {
    name: 'Agent Commission',
    ref: 'Insurance Policy',
    file: 'agent_commission',
    query: `select
	agent,
	policy_number,
	client,
	provider,
	premium_amount,
	commission_rate,
	commission_amount,
	status
from \`tabInsurance Policy\`
where docstatus < 2
order by commission_amount desc`,
  },
  {
    name: 'Policy Claim',
    ref: 'Insurance Claim',
    file: 'policy_claim',
    query: `select
	claim_number,
	policy,
	client,
	claim_type,
	incident_date,
	claimed_amount,
	approved_amount,
	status
from \`tabInsurance Claim\`
where docstatus < 2
order by incident_date desc`,
  },
  {
    name: 'Policy Sale',
    ref: 'Insurance Policy',
    file: 'policy_sale',
    query: `select
	policy_number,
	policy_type,
	client,
	scheme,
	coverage_level,
	start_date,
	premium_amount,
	status
from \`tabInsurance Policy\`
where docstatus < 2
order by start_date desc`,
  },
]

for (const r of reports) {
  const dir = path.join(MOD, 'report', r.file)
  write(
    path.join(dir, `${r.file}.json`),
    JSON.stringify(
      {
        add_total_row: 1,
        columns: [],
        creation: '2026-09-04 06:00:00',
        disabled: 0,
        docstatus: 0,
        doctype: 'Report',
        filters: [],
        idx: 0,
        is_standard: 'Yes',
        letterhead: null,
        modified: '2026-09-04 06:00:00',
        modified_by: 'Administrator',
        module: 'Insurance',
        name: r.name,
        owner: 'Administrator',
        prepared_report: 0,
        ref_doctype: r.ref,
        report_name: r.name,
        report_type: 'Query Report',
        roles: [
          { role: 'Insurance Manager' },
          { role: 'Insurance Agent' },
          { role: 'System Manager' },
        ],
        query: r.query,
      },
      null,
      1
    )
  )
  write(path.join(dir, `${r.file}.js`), `frappe.query_reports['${r.name}'] = { filters: [] };\n`)
  write(path.join(dir, `${r.file}.py`), 'import frappe\n\n\ndef execute(filters=None):\n\treturn [], []\n')
  write(path.join(dir, '__init__.py'), '')
}
write(path.join(MOD, 'report', '__init__.py'), '')

write(
  path.join(MOD, 'workspace', 'insurance', 'insurance.json'),
  JSON.stringify(
    {
      charts: [],
      content: '[]',
      creation: '2026-09-04 06:00:00',
      docstatus: 0,
      doctype: 'Workspace',
      for_user: '',
      hide_custom: 0,
      icon: 'shield',
      idx: 0,
      is_hidden: 0,
      label: 'Insurance',
      links: [
        { label: 'Masters', type: 'Card Break' },
        { label: 'Insurance Provider', type: 'Link', link_type: 'DocType', link_to: 'Insurance Provider', onboarding: 0 },
        { label: 'Insurance Scheme', type: 'Link', link_type: 'DocType', link_to: 'Insurance Scheme' },
        { label: 'Transactions', type: 'Card Break' },
        { label: 'Insurance Policy', type: 'Link', link_type: 'DocType', link_to: 'Insurance Policy' },
        { label: 'Insurance Claim', type: 'Link', link_type: 'DocType', link_to: 'Insurance Claim' },
        { label: 'Insurance Client', type: 'Link', link_type: 'DocType', link_to: 'Insurance Client' },
        { label: 'Operations', type: 'Card Break' },
        { label: 'Compliance Record', type: 'Link', link_type: 'DocType', link_to: 'Compliance Record' },
        { label: 'Insurance Communication', type: 'Link', link_type: 'DocType', link_to: 'Insurance Communication' },
        { label: 'Reports', type: 'Card Break' },
        { label: 'Agent Commission', type: 'Link', link_type: 'Report', link_to: 'Agent Commission', is_query_report: 1 },
        { label: 'Policy Claim', type: 'Link', link_type: 'Report', link_to: 'Policy Claim', is_query_report: 1 },
        { label: 'Policy Sale', type: 'Link', link_type: 'Report', link_to: 'Policy Sale', is_query_report: 1 },
      ],
      modified: '2026-09-04 06:00:00',
      modified_by: 'Administrator',
      module: 'Insurance',
      name: 'Insurance',
      owner: 'Administrator',
      parent_page: '',
      public: 1,
      restrict_to_domain: '',
      roles: [{ role: 'Insurance Manager' }, { role: 'Insurance Agent' }, { role: 'System Manager' }],
      sequence_id: 1.0,
      shortcuts: [
        { label: 'Insurance Policy', type: 'DocType', link_to: 'Insurance Policy', color: 'Blue', stats_filter: '{"status":["=","Active"]}', format: '{} Active' },
        { label: 'Insurance Claim', type: 'DocType', link_to: 'Insurance Claim', color: 'Orange' },
        { label: 'Agent Commission', type: 'Report', link_to: 'Agent Commission', is_query_report: 1 },
      ],
      title: 'Insurance',
    },
    null,
    1
  )
)
write(path.join(MOD, 'workspace', 'insurance', '__init__.py'), '')
write(path.join(MOD, 'workspace', '__init__.py'), '')

write(
  path.join(PKG, 'fixtures', 'role.json'),
  JSON.stringify(
    [
      { doctype: 'Role', name: 'Insurance Manager', role_name: 'Insurance Manager', desk_access: 1, is_custom: 1 },
      { doctype: 'Role', name: 'Insurance Agent', role_name: 'Insurance Agent', desk_access: 1, is_custom: 1 },
      { doctype: 'Role', name: 'Claims Adjuster', role_name: 'Claims Adjuster', desk_access: 1, is_custom: 1 },
      { doctype: 'Role', name: 'Compliance Officer', role_name: 'Compliance Officer', desk_access: 1, is_custom: 1 },
      { doctype: 'Role', name: 'Insurance User', role_name: 'Insurance User', desk_access: 1, is_custom: 1 },
    ],
    null,
    1
  )
)

write(
  path.join(APP, 'pyproject.toml'),
  `[project]
name = "insurance"
authors = [{ name = "Aegis", email = "hello@aegis.local" }]
description = "Insurance ERP"
requires-python = ">=3.10"
readme = "README.md"
dynamic = ["version"]
dependencies = []

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.bench.frappe-dependencies]
frappe = ">=15.0.0"
`
)

write(
  path.join(APP, 'README.md'),
  `# Insurance

Frappe app for insurance operations. Install on a bench next to CRM, Helpdesk, and ERPNext.

\`\`\`
bench get-app ./insurance
bench --site <site> install-app insurance
\`\`\`

## Layout

\`\`\`
insurance/
  insurance/
    hooks.py
    modules.txt
    insurance/
      doctype/
        insurance_provider/
        insurance_scheme/
        insurance_policy/
        insurance_claim/
        insurance_client/
        compliance_record/
        insurance_communication/
      report/
        agent_commission/
        policy_claim/
        policy_sale/
      workspace/
        insurance/
\`\`\`

Roles: Insurance Manager, Insurance Agent, Claims Adjuster, Compliance Officer, Insurance User.
Integrations load only when the matching app is installed (\`crm\`, \`helpdesk\`, \`erpnext\`).
`
)

write(path.join(APP, 'license.txt'), 'MIT License\n')

console.log('Generated Frappe app at', APP)
console.log('DocTypes:', Object.keys(doctypes).join(', '))
