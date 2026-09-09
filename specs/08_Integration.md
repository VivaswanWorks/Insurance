# Integration Guide – Insurance Management App with other Frappe Apps

This document instructs coding agents how to integrate the Insurance Management app with standard and popular Frappe / ERPNext ecosystem apps.

## General Principles
1. Prefer **Link** and **Dynamic Link** fields over duplicating data.
2. Use **hooks** (`doc_events`, `override_doctype_class`, `fixtures`) for clean extension.
3. Keep Insurance app installable independently; make integrations optional via `hooks.py` checks or feature flags.
4. Always respect permissions of the target app.
5. Use `frappe.get_cached_doc` / `frappe.db.get_value` for performance.
6. For accounting impact, create **Journal Entry** or **Payment Entry** rather than direct GL manipulation.

---

## 1. ERPNext (Accounting, Selling, Buying, Stock)

### Customer / Supplier
- `Insurance Policy.client` → Dynamic Link to **Customer**
- `Insurance Provider` can also be a **Supplier** (for premium payables / commission)
- On Policy submit: optionally create / update Customer if not exists

### Accounting
- Map accounts on Insurance Provider & Company:
  - Premium Income
  - Claims Expense / Claims Payable
  - Commission Expense / Payable
  - GST / Tax accounts
- On Claim Settlement → create **Payment Entry** or **Journal Entry**
- On Premium receipt → **Payment Entry** against Customer / Policy
- Use **Payment Terms** and **Payment Entry** for installment premiums

### Items / Sales Invoice (optional)
- Create Item for each major Scheme (non-stock)
- Generate Sales Invoice for premium billing if required by finance team

### Hooks Example
```python
# hooks.py
doc_events = {
    "Insurance Policy": {
        "on_submit": "insurance_core.integrations.erpnext.create_accounting_entries",
    },
    "Insurance Claim": {
        "on_update_after_submit": "insurance_core.integrations.erpnext.handle_claim_settlement",
    }
}
```

---

## 2. HRMS (Human Resource Management)

### Employee as Insured / Proposer
- `Policy Member.employee` → Link to **Employee**
- `Insurance Policy.client_type = "Employee"`
- Group policies for company employees (employer-employee schemes)

### Payroll Integration
- Deduct premium from salary (create additional salary component)
- On Policy creation for Employee → optional Additional Salary entry
- Claim reimbursement via Expense Claim or additional salary

### Hooks
- When Employee is relieved → flag related policies for review
- Auto-create group policy members from Employee list (filtered by Department / Grade)

---

## 3. CRM

### Lead → Opportunity → Policy
- Create **Insurance Opportunity** from CRM Lead / Opportunity
- On “Won” → create Insurance Policy (or Proposal)
- Map custom fields: interested scheme, expected premium, source

### Customer 360
- Add Insurance dashboard to Customer form (Web View or custom HTML field)
- Show active policies, open claims, total premium

### Campaign
- Link marketing Campaign to scheme-specific quote generation

---

## 4. Helpdesk

### Ticket ↔ Claim / Policy
- Custom field on **HD Ticket**: `insurance_policy`, `insurance_claim`
- Button on Ticket: “Create Claim” or “Link to Existing Claim”
- When Claim status changes → update linked Ticket status / add comment
- SLA: map Helpdesk SLA to claim response TATs

### Grievance Redressal
- Use Helpdesk as the grievance system; tag tickets with “Insurance Grievance”
- Mandatory fields via custom form for IRDAI compliance

---

## 5. Insights (Analytics)

### Recommended Dashboards & Queries
- Policy Portfolio: Active policies by scheme, provider, geography
- Premium Dashboard: Collection vs Target, Outstanding, Renewal rate
- Claims Dashboard: Incurred Claim Ratio (ICR), Average settlement days, Rejection %
- Client Analytics: Lifetime value, cross-sell opportunities, lapse rate
- Compliance: Checklist completion %, overdue regulatory reports

### Implementation
- Create **Insights Query** / **Dashboard** as fixtures or via setup wizard
- Use Insurance DocTypes as data sources
- Add custom scripts for calculated metrics (e.g. ICR = Claims Paid / Premium * 100)

---

## 6. Healthcare

### Patient as Insured
- `Policy Member.patient` → Link to **Patient**
- Health / Mediclaim policies linked to Patient
- On Claim (Cashless): pull diagnosis, admission, discharge from Healthcare Patient Encounter / Inpatient Record

### Integration Points
- Button on Patient form: “View Insurance Policies”
- Auto-fetch Patient demographics into Policy Member
- Pre-authorization request from Healthcare → create Claim draft

---

## 7. Other Useful Integrations

### Frappe HR (if separate) / Attendance
- Already covered under HRMS

### Lending / Loan Management (if present)
- Credit-linked insurance (loan protection)
- Link Policy to Loan

### WhatsApp / SMS Apps
- See Automated Communications module

### E-Invoice / GST
- Generate e-invoice for premium invoices if required

### Digital Signature / eSign
- Integrate for policy document signing (via third-party or Frappe app)

---

## Installation & Feature Flags

In `hooks.py` or a setup wizard:
```python
# Optional integrations
app_include_js = ...
after_install = "insurance_core.install.after_install"

def after_install():
    if "erpnext" in frappe.get_installed_apps():
        create_erpnext_custom_fields()
    if "hrms" in frappe.get_installed_apps():
        create_hrms_custom_fields()
    # similarly for others
```

Provide a **Setup Wizard** or **Insurance Settings** page where admin can enable/disable specific integrations.

---

## Testing Matrix for Agents
| Integration | Test Case |
|-------------|-----------|
| ERPNext | Policy submit creates correct JE / PE |
| HRMS | Employee policy appears in Employee form |
| CRM | Lead converted to Policy |
| Helpdesk | Ticket linked to Claim updates both ways |
| Healthcare | Patient data flows into Claim |
| Insights | Dashboard shows live numbers |

---

## Version Compatibility
- Target Frappe v15 / ERPNext v15+
- Use `frappe.get_meta` and feature detection to stay compatible with future versions
- Document minimum required versions of each integrated app
