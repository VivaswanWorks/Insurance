# Policy Management Module

## Purpose
Core transactional DocType that represents an issued insurance policy for a client (individual, family, or corporate group). Tracks coverage, premium, members, endorsements, renewals, and status lifecycle.

## DocType: Insurance Policy

### Naming
- Naming Series: `POL-.YYYY.-.#####`
- Title Field: `policy_number` (or combination of scheme + client)

### Fields – Header

| Fieldname | Label | Type | Options / Details | Mandatory |
|-----------|-------|------|-------------------|-----------|
| policy_number | Policy Number | Data | Unique (from insurer or internal) | Yes |
| naming_series | Series | Select | | |
| insurance_scheme | Insurance Scheme | Link | Insurance Scheme | Yes |
| insurance_provider | Insurance Provider | Link | Insurance Provider | Read-only (fetched) |
| policy_type | Policy Type | Select | New, Renewal, Endorsement, Migration | Yes |
| status | Status | Select | Draft, Active, Lapsed, Cancelled, Expired, Claimed, Settled | Yes | Default: Draft |
| client | Client | Dynamic Link | Customer / Employee / Patient / Lead | Yes |
| client_type | Client Type | Select | Customer, Employee, Patient, Lead | Yes |
| party | Party | Dynamic Link | based on client_type | |
| start_date | Policy Start Date | Date | | Yes |
| end_date | Policy End Date | Date | | Yes |
| issue_date | Issue Date | Date | | |
| proposal_number | Proposal / Quote No. | Data | | |
| previous_policy | Previous Policy | Link | Insurance Policy | | for renewals |

#### Sum Insured & Premium
| Fieldname | Label | Type |
|-----------|-------|------|
| sum_insured | Total Sum Insured | Currency |
| premium_amount | Net Premium | Currency |
| tax_amount | Tax / GST | Currency |
| total_premium | Total Premium | Currency | Read-only (calculated) |
| premium_frequency | Premium Frequency | Select: Monthly, Quarterly, Half-Yearly, Yearly, Single |
| next_premium_due | Next Premium Due Date | Date |
| payment_status | Payment Status | Select: Unpaid, Partially Paid, Paid, Overdue |

#### Members / Beneficiaries (for Health / Life / Group)
Child Table: `policy_members` → **Policy Member**

| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| member_name | Member Name | Data | |
| relationship | Relationship | Select: Self, Spouse, Child, Parent, Other | |
| date_of_birth | Date of Birth | Date | |
| age | Age | Int | Read-only |
| gender | Gender | Select | |
| sum_insured | Sum Insured (Member) | Currency | |
| id_proof_type | ID Proof Type | Select | |
| id_proof_number | ID Proof Number | Data | |
| is_primary | Primary Member | Check | |
| employee | Employee | Link | Employee | if HRMS linked |
| patient | Patient | Link | Patient | if Healthcare linked |

#### Coverage Snapshot (copied from Scheme at issuance, editable via Endorsement)
Child Table: `policy_coverages` → same structure as Scheme Coverage Item

#### Documents & Attachments
| Fieldname | Label | Type |
|-----------|-------|------|
| policy_document | Policy Document (PDF) | Attach |
| proposal_form | Proposal Form | Attach |
| other_documents | Other Documents | Table | Policy Document |

### Child: Policy Document
| Fieldname | Label | Type |
|-----------|-------|------|
| document_type | Type | Select: Policy Copy, Endorsement, Certificate, Other |
| attachment | File | Attach |
| uploaded_on | Uploaded On | Datetime | Read-only |

### Endorsements
Separate DocType: **Policy Endorsement**
- Linked to Insurance Policy
- Types: Member Addition/Deletion, Sum Insured Change, Address Change, Nominee Change, Correction, Cancellation
- Status workflow: Draft → Submitted → Approved → Applied
- On “Apply”: update parent Policy fields + create version history

### Renewals
- Button / Action: “Create Renewal”
- Creates new Policy with `policy_type = Renewal`, links `previous_policy`
- Copies members, adjusts ages, recalculates premium from current scheme rates
- Option to carry forward No-Claim Bonus / Loyalty discount

### Status Workflow
```
Draft → Active → (Lapsed / Expired / Cancelled)
Active → Claimed (when claim is open)
Claimed → Settled
```

### Business Rules
- `end_date` must be > `start_date`
- On submit: validate premium calculation, required members, documents
- Auto-set `status = Expired` via daily scheduler when `end_date < today` and no renewal
- Grace period handling for premium payment
- Prevent editing of key fields after submit (use Endorsement)

### Permissions
- Insurance Manager: Full + Submit + Cancel
- Insurance User: Create, Write (Draft), Read
- Client Portal User: Read own policies only

### List / Report Views
- Active Policies
- Policies Expiring in 30/60/90 days
- Premium Due
- Policies by Scheme / Provider / Client Type

### Dashboard
- Total Active Policies
- Premium Collected (MTD / YTD)
- Expiring Soon
- Claims Ratio
