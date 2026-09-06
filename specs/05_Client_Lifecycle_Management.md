# Client Lifecycle Management Module

## Purpose
Track the complete customer journey: Lead / Prospect → Quote → Proposal → Policyholder → Active Customer → Renewal → Lapsed / Win-back. Provides a 360° view of the client across policies, claims, communications, and interactions.

## Core Concepts
- **Client** can be:
  - Customer (ERPNext)
  - Employee (HRMS)
  - Patient (Healthcare)
  - Lead / Opportunity (CRM)
- Use Dynamic Link + client_type pattern consistently across Policy, Claim, Quote.

## DocType: Insurance Opportunity / Quote (optional but recommended)

### Fields
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| opportunity_from | Opportunity From | Select | Lead, Customer, Employee, Patient, Campaign |
| party | Party | Dynamic Link | |
| insurance_scheme | Interested Scheme | Link | Insurance Scheme |
| expected_premium | Expected Premium | Currency |
| probability | Probability % | Percent |
| stage | Stage | Select | Prospect, Needs Analysis, Quote Sent, Negotiation, Won, Lost |
| assigned_to | Assigned To | Link | User |
| next_follow_up | Next Follow-up | Datetime |
| source | Source | Link | Lead Source / Campaign |

## 360° Client View (Custom Page / Dashboard)
Recommended sections:
1. **Profile** – basic details, KYC status, risk category
2. **Active Policies** – list with status, expiry, premium
3. **Claims History** – open + closed claims
4. **Communication Log** – emails, calls, SMS, WhatsApp (via Automated Communications)
5. **Quotes / Opportunities**
6. **Documents / KYC**
7. **Family / Group Members** (if applicable)
8. **Timeline** – all events chronologically

## KYC & Onboarding
DocType: **Client KYC**
- Linked to Party
- Fields: ID proofs, address proof, photograph, income proof, medical reports (for life/health)
- Status: Pending, Verified, Rejected, Expired
- Expiry tracking + renewal reminders

## Risk Profiling
- Optional DocType or fields on Customer:
  - Risk Category: Low / Medium / High
  - Smoking / Lifestyle flags
  - Pre-existing conditions summary
  - Credit / financial score (if integrated)

## Lifecycle Stages (to be maintained on Customer or custom field)
- Prospect
- Quoted
- Policyholder
- Active
- At Risk (near expiry / missed premium)
- Lapsed
- Win-back
- Blacklisted

## Automation Hooks
- When Policy is submitted → update Client stage to Policyholder / Active
- When Policy expires without renewal → stage = Lapsed + create Opportunity for win-back
- High-value client flag based on total premium or number of policies

## Permissions
- Sales / CRM User: Opportunities + limited client view
- Insurance User: Full client 360 for assigned clients
- Insurance Manager: All clients

## Integration Points
- CRM: Lead → Opportunity → Customer
- HRMS: Employee as insured / proposer
- Healthcare: Patient as insured
- ERPNext Customer: single source of truth for retail / corporate clients
