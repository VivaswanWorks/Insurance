# Client Eligibility Criteria Module

## Purpose
Define, evaluate, and score eligibility conditions that determine whether a claim can be successfully filed and approved. Acts as a configurable rules engine that runs at claim intake (and optionally at policy issuance) to surface risks early, enforce mandatory prerequisites, and compute a **Claim Success Score**.

Supports both hard gates (Mandatory → block claim submission) and soft signals (Optional → reduce/increase success weightage).

## DocType: Client Eligibility Criteria

### Naming
- Naming Series: `ELC-.YYYY.-.#####`
- Title Field: `criteria_name`

### Fields – Header

| Fieldname | Label | Type | Options / Details | Mandatory |
|-----------|-------|------|-------------------|-----------|
| criteria_name | Criteria Name | Data | Unique | Yes |
| criteria_code | Criteria Code | Data | Unique short code (e.g. KYC_COMPLETE) | Yes |
| description | Description | Small Text | | |
| applies_to | Applies To | Select | All Schemes, Specific Scheme Type, Specific Scheme, Specific Provider | Yes |
| scheme_type | Scheme Type | Select | Life, Health, Motor, Property, Liability, Travel, Cyber, Marine, Other | | Conditional |
| insurance_scheme | Insurance Scheme | Link | Insurance Scheme | | Conditional |
| insurance_provider | Insurance Provider | Link | Insurance Provider | | Conditional |
| claim_type | Applicable Claim Type | Select | All, Cashless, Reimbursement, Third Party, Death, Disability, Property, Other | Default: All |
| status | Status | Select | Active, Inactive | Yes | Default: Active |
| evaluation_stage | Evaluation Stage | Select | Policy Issuance, Claim Intake, Both, Pre-Authorization | Yes | Default: Claim Intake |
| is_system | Is System Criteria | Check | | | Protected from deletion if set |

#### Scoring & Enforcement
| Fieldname | Label | Type | Options / Details | Mandatory |
|-----------|-------|------|-------------------|-----------|
| is_mandatory | Mandatory | Check | | Yes | If checked → claim cannot be submitted unless passed |
| weightage | Weightage (%) | Percent | 0–100 | Yes | Contribution to overall Claim Success Score |
| pass_score | Minimum Pass Score (if scored) | Percent | | | For multi-condition criteria |
| failure_action | Failure Action | Select | Block Submission, Warning Only, Require Override, Auto-Reject | Yes |
| override_role | Override Allowed For Role | Link | Role | | Only if Failure Action = Require Override |
| severity | Severity | Select | Critical, High, Medium, Low | Yes | Default: Medium |

#### Evaluation Logic
| Fieldname | Label | Type | Options / Details |
|-----------|-------|------|-------------------|
| evaluation_method | Evaluation Method | Select | Field Check, Expression, Script, External API, Checklist | Yes |
| source_doctype | Source DocType | Link | DocType | | e.g. Insurance Policy, Customer, Patient, Employee |
| field_to_check | Field to Check | Data | | | Fieldname on source |
| expected_value | Expected Value | Data | | | Or use operator |
| operator | Operator | Select | Equals, Not Equals, Greater Than, Less Than, In, Not In, Is Set, Is Not Set, Contains | |
| python_expression | Python Expression | Code | | | Safe eval context with `doc`, `policy`, `claim`, `client` |
| custom_script | Custom Script Path | Data | | | dotted path to method |
| external_api | External API Endpoint | Data | | | For credit score, blacklist, medical underwriting APIs |
| checklist_items | Checklist Items | Table | Eligibility Checklist Item | |

### Child DocType: Eligibility Checklist Item
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| item | Checklist Item | Data | |
| is_mandatory | Mandatory | Check | |
| weightage | Weightage (%) | Percent | |
| evidence_required | Evidence / Attachment Required | Check | |
| help_text | Help Text | Small Text | |

---

## DocType: Claim Eligibility Evaluation (Transactional Log)

Created automatically when a Claim is saved / submitted. Stores the snapshot of every criteria result for audit.

### Fields
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| insurance_claim | Insurance Claim | Link | Insurance Claim | Yes |
| insurance_policy | Insurance Policy | Link | Insurance Policy | |
| evaluation_datetime | Evaluated On | Datetime | Read-only |
| overall_score | Claim Success Score (%) | Percent | Read-only |
| overall_status | Overall Status | Select | Eligible, Conditionally Eligible, Not Eligible | Read-only |
| can_submit | Can Submit Claim | Check | Read-only |
| evaluated_by | Evaluated By | Link | User | Read-only |
| criteria_results | Criteria Results | Table | Claim Eligibility Result | |
| override_reason | Override Reason | Small Text | | If manager overrode |
| overridden_by | Overridden By | Link | User | |

### Child: Claim Eligibility Result
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| eligibility_criteria | Eligibility Criteria | Link | Client Eligibility Criteria | |
| is_mandatory | Was Mandatory | Check | Read-only |
| weightage | Weightage | Percent | Read-only |
| result | Result | Select | Pass, Fail, Skipped, Error | |
| score_contribution | Score Contribution | Percent | |
| remarks | Remarks / Failure Reason | Small Text | |
| evidence | Evidence Attachment | Attach | |

---

## Pre-seeded / Recommended Eligibility Criteria

Agents should create these as fixtures or via setup wizard (all Active, appropriate weightages):

| Code | Name | Mandatory | Weightage | Failure Action | Typical Check |
|------|------|-----------|-----------|----------------|---------------|
| KYC_COMPLETE | KYC Documents Complete & Verified | Yes | 15 | Block Submission | Client KYC status = Verified |
| POLICY_ACTIVE | Policy is Active | Yes | 20 | Block Submission | Policy.status = Active |
| WITHIN_COVERAGE | Incident within Policy Period | Yes | 15 | Block Submission | incident_date between start_date & end_date |
| WAITING_PERIOD | Waiting Period Completed | Yes | 10 | Block Submission | incident_date > start_date + waiting_period_days |
| PRE_EXISTING | Pre-existing Disease Waiting Over | No | 8 | Warning Only | For health claims |
| PREMIUM_PAID | Premium Paid / No Outstanding Dues | Yes | 10 | Block Submission | payment_status = Paid |
| SUM_INSURED_AVAILABLE | Sufficient Sum Insured Remaining | Yes | 10 | Block Submission | claimed_amount ≤ remaining coverage |
| DOCUMENTS_COMPLETE | Mandatory Claim Documents Attached | Yes | 12 | Block Submission | Checklist of required docs present |
| NO_FRAUD_FLAG | No Fraud / Blacklist Flag | Yes | 15 | Block Submission | Client not in blacklist / previous fraud |
| MEMBER_COVERED | Claimant is Covered Member | Yes | 10 | Block Submission | Claimant exists in policy_members |
| NETWORK_HOSPITAL | Treatment at Network Hospital (Cashless) | No | 5 | Warning Only | For cashless claims |
| INTIMATION_TIMELY | Claim Intimated within Allowed Days | Yes | 8 | Require Override | reported_date – incident_date ≤ configured days |
| AGE_ELIGIBLE | Member Age within Scheme Limits | No | 5 | Warning Only | Age between min/max at inception or claim |
| EXCLUSION_CHECK | Incident not under Exclusions | Yes | 10 | Block Submission | Manual or keyword / ICD check |
| CONSENT_VALID | Valid Consent / Authorization Present | No | 3 | Warning Only | For data sharing / TPA |

> Weightages above are illustrative; total of active mandatory + optional criteria should be normalized to 100% at evaluation time or kept as absolute contribution.

---

## Business Logic & Evaluation Engine

### Method: `evaluate_claim_eligibility(claim_doc)`
1. Fetch all Active `Client Eligibility Criteria` matching:
   - applies_to (scheme / type / provider)
   - claim_type
   - evaluation_stage contains “Claim Intake”
2. For each criteria:
   - Run evaluation_method (field check / expression / script / API / checklist)
   - Record Pass / Fail + contribution
3. Calculate:
   ```
   overall_score = sum(score_contribution of passed criteria)
   ```
4. Determine overall_status:
   - **Not Eligible** → any Mandatory criteria failed and Failure Action = Block Submission
   - **Conditionally Eligible** → Mandatory passed but overall_score < configured threshold (default 70) or warnings present
   - **Eligible** → all Mandatory passed and score ≥ threshold
5. Set `can_submit` flag
6. Create / update `Claim Eligibility Evaluation` log
7. If Not Eligible → `frappe.throw` with clear list of failed mandatory criteria (unless override)

### Override Flow
- Role defined in `override_role` can force submit
- Must provide `override_reason`
- Logged in evaluation record + Communication / Comment on Claim

### Hooks
```python
# on Insurance Claim
def validate(self):
    if self.is_new() or self.has_value_changed("claimed_amount") or ...:
        from insurance_core.eligibility import evaluate_claim_eligibility
        result = evaluate_claim_eligibility(self)
        if not result.can_submit and not self.flags.ignore_eligibility:
            frappe.throw(...)
```

### Scheduler / Recalculation
- Button on Claim: “Re-evaluate Eligibility”
- Optional daily job to re-score open claims if underlying data (KYC, premium status) changes

---

## Insurance Settings Additions
Add to **Insurance Settings** (Single):
| Fieldname | Label | Type | Default |
|-----------|-------|------|---------|
| eligibility_score_threshold | Minimum Claim Success Score (%) | Percent | 70 |
| enable_eligibility_engine | Enable Eligibility Engine | Check | 1 |
| eligibility_override_role | Default Override Role | Link | Role | Insurance Manager |
| max_intimation_days | Max Days for Claim Intimation | Int | 30 |
| normalize_weightage | Normalize Weightages to 100% | Check | 1 |

---

## Permissions
- Insurance Manager: Full CRUD on Client Eligibility Criteria
- Claims Assessor / Insurance User: Read criteria + full access to Claim Eligibility Evaluation
- System Manager: Full
- Client Portal: No access (internal only)

---

## Reports & Dashboards
- Eligibility Failure Analysis (most failed criteria)
- Average Claim Success Score by Scheme / Provider
- Override Frequency & Reasons
- Claims blocked vs proceeded after override
- Trend of score vs actual approval / repudiation (feedback loop for tuning weightages)

---

## API Methods
- `insurance_core.eligibility.evaluate_claim_eligibility(claim_name)`
- `insurance_core.eligibility.get_applicable_criteria(scheme, claim_type)`
- `insurance_core.eligibility.recalculate_score(claim_name)`

---

## Integration Points
- **Client Lifecycle / KYC** → KYC_COMPLETE criteria
- **Policy Management** → POLICY_ACTIVE, PREMIUM_PAID, MEMBER_COVERED, WITHIN_COVERAGE
- **Claims Management** → runs at validate / before_submit
- **Compliance** → document checklist items can link to Compliance Checklist Template
- **External** → credit bureaus, fraud databases, medical underwriting APIs via `external_api`

---

## Development Notes for Coding Agents
1. Keep evaluation pure and side-effect free except for writing the Evaluation log.
2. Use `frappe.utils.safe_eval` for python_expression with restricted context.
3. Cache applicable criteria per scheme (clear on criteria update).
4. Make weightage normalization optional but recommended.
5. All user-facing failure messages must be clear and actionable (“KYC is not verified – please complete KYC before filing claim”).
6. Write unit tests for each evaluation_method and for mandatory vs optional behaviour.
7. Version the criteria (or keep change log) so historical evaluations remain explainable.
