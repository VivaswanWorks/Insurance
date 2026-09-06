# Compliance Tracking Module

## Purpose
Ensure the insurance operations stay compliant with IRDAI (or local regulator) guidelines, internal policies, data protection (GDPR / local), and audit requirements. Automate document generation, retention, and regulatory reporting.

## Key Features

### 1. Regulatory Document Register
DocType: **Compliance Document**
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| document_title | Title | Data | |
| document_type | Type | Select | Policy Wording, Rate Filing, Board Resolution, Audit Report, IRDAI Circular, Internal SOP, Other |
| regulator | Regulator | Select | IRDAI, SEBI, RBI, Local, Internal |
| version | Version | Data | |
| effective_from | Effective From | Date | |
| effective_to | Effective To | Date | |
| attachment | File | Attach | |
| responsible_user | Owner | Link | User |
| status | Status | Select | Draft, Active, Superseded, Archived |
| related_schemes | Related Schemes | Table MultiSelect | Insurance Scheme |

### 2. Policy & Claim Audit Trail
- All critical DocTypes (Policy, Claim, Endorsement, Provider) must have:
  - Full versioning enabled
  - Comment / Activity log
  - Optional: custom Audit Log child table for sensitive field changes

### 3. Mandatory Document Checklist
Configurable per Scheme Type or Claim Type:
- DocType: **Compliance Checklist Template**
- On Policy / Claim creation → auto-create checklist items
- User must mark each as Completed + attach evidence before submit / settlement

### 4. Regulatory Reporting
- Scheduled reports / data exports:
  - Active Policies by Scheme
  - Claims Paid / Outstanding
  - Premium Income
  - Commission paid to intermediaries
  - Grievance Redressal statistics
- Export formats: Excel, CSV, XML (as required by regulator)
- Store generated reports as **Compliance Report** DocType with period + attachment

### 5. Data Retention & Archival
- Configurable retention periods (e.g. Policies – 8 years after expiry, Claims – 5 years after settlement)
- Scheduler job to flag records for archival / anonymization
- Soft-delete or move to archive site

### 6. Consent & Privacy
- Track customer consent for:
  - Data processing
  - Marketing communications
  - Sharing with TPAs / reinsurers
- Link to Communication preferences

### 7. Grievance / Complaint Tracking
- Either use Helpdesk or dedicated **Insurance Grievance** DocType
- Mandatory fields: nature of complaint, policy/claim reference, resolution timeline (as per IRDAI TAT)
- Escalation matrix
- Monthly grievance report

## Permissions
- Compliance Officer: Full on Compliance Document & Reports
- Insurance Manager: Read + limited write
- Auditor role: Read-only on all transactional + compliance docs

## Alerts & Notifications
- License / Agreement expiring (Provider)
- Checklist incomplete before policy issue
- Regulatory report due dates
- High grievance volume

## Audit Hooks
- Override `on_submit` / `on_cancel` of Policy & Claim to write immutable audit entries
- Prevent deletion of submitted compliance-critical documents
