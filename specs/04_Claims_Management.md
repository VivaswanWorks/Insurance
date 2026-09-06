# Claims Management Module

## Purpose
End-to-end claims lifecycle: intake → documentation → assessment → approval → settlement → recovery / repudiation. Supports cashless, reimbursement, and third-party claims.

## DocType: Insurance Claim

### Naming
- Naming Series: `CLM-.YYYY.-.#####`
- Title Field: `claim_number` or combination of policy + incident date

### Fields – Header

| Fieldname | Label | Type | Options / Details | Mandatory |
|-----------|-------|------|-------------------|-----------|
| claim_number | Claim Number | Data | Unique | Yes |
| insurance_policy | Insurance Policy | Link | Insurance Policy | Yes |
| insurance_scheme | Insurance Scheme | Link | Insurance Scheme | Read-only |
| insurance_provider | Insurance Provider | Link | Insurance Provider | Read-only |
| claimant | Claimant | Dynamic Link | Customer / Employee / Patient | Yes |
| claim_type | Claim Type | Select | Cashless, Reimbursement, Third Party, Death, Disability, Property, Other | Yes |
| claim_status | Status | Select | Draft, Submitted, Under Review, Additional Info Required, Approved, Partially Approved, Rejected, Settled, Closed | Yes |
| incident_date | Date of Incident / Loss | Date | | Yes |
| reported_date | Date Reported | Date | | Yes |
| intimation_mode | Intimation Mode | Select | Portal, Email, Phone, Branch, TPA, Other | |
| description | Incident Description | Text Editor | | Yes |

#### Financials
| Fieldname | Label | Type |
|-----------|-------|------|
| claimed_amount | Claimed Amount | Currency |
| approved_amount | Approved Amount | Currency |
| settled_amount | Settled Amount | Currency |
| deductible | Deductible / Excess | Currency |
| co_pay | Co-pay Amount | Currency |
| currency | Currency | Link | Currency |

#### Hospital / Service Provider (Health claims)
| Fieldname | Label | Type |
|-----------|-------|------|
| hospital | Hospital / Provider | Link | Supplier or custom Healthcare Provider |
| admission_date | Admission Date | Date |
| discharge_date | Discharge Date | Date |
| diagnosis | Diagnosis / ICD Code | Data / Small Text |
| treatment_details | Treatment Details | Text Editor |

#### Documents
Child Table: `claim_documents` → **Claim Document**

| Fieldname | Label | Type |
|-----------|-------|------|
| document_type | Document Type | Select: Discharge Summary, Bills, Reports, ID Proof, FIR, Estimate, Other |
| attachment | Attachment | Attach |
| uploaded_by | Uploaded By | Link | User | Read-only |
| uploaded_on | Uploaded On | Datetime | Read-only |
| verified | Verified | Check |

#### Assessment & Decision
| Fieldname | Label | Type |
|-----------|-------|------|
| assessor | Assessor / Surveyor | Link | User / Employee |
| assessment_date | Assessment Date | Date |
| assessment_notes | Assessment Notes | Text Editor |
| decision | Decision | Select: Approve, Partial Approve, Reject, Investigate |
| rejection_reason | Rejection Reason | Small Text |
| approval_authority | Approval Authority | Link | User |

#### Settlement
| Fieldname | Label | Type |
|-----------|-------|------|
| settlement_mode | Settlement Mode | Select: Bank Transfer, Cheque, Cash, Adjustment |
| settlement_date | Settlement Date | Date |
| payment_entry | Payment Entry | Link | Payment Entry | (ERPNext) |
| settlement_reference | Settlement Reference / UTR | Data |
| recovery_amount | Recovery / Salvage | Currency |

### Workflow States
1. Draft
2. Submitted (Intimated)
3. Under Review
4. Additional Info Required
5. Approved / Partially Approved / Rejected
6. Settled
7. Closed

### Business Logic
- On submit: notify provider / TPA if configured
- Validate claimed_amount against policy sum_insured & remaining coverage
- Auto-create To-Do / Task for assessor
- On approval: create accounting entries (Claims Payable → Bank / Expense)
- Link to Helpdesk Ticket if customer raised via support
- Prevent settlement if documents incomplete (configurable)

### Child / Related DocTypes
- **Claim Assessment Log** (timeline of status changes + comments)
- **Claim Recovery** (for subrogation / third-party recovery)

### Permissions
- Insurance Claims User: Create, Write (own), Read
- Claims Assessor: Update assessment fields
- Insurance Manager: Full + Approve + Settle
- Finance User: Settlement related

### Reports & Dashboards
- Claims Aging
- Claims Ratio by Scheme / Provider
- Average Settlement Time
- Rejection Analysis
- Outstanding Claims Liability

### Notifications
- Claim Submitted → Client + Internal team
- Additional Info Required → Client
- Approved / Rejected → Client
- Settled → Client + Finance
