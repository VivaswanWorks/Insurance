# Insurance Management App – Overview & Additional Features

## Core Modules (from original requirements)
1. **Insurance Provider** – Master data for insurers, TPAs, brokers
2. **Insurance Scheme** – Product / plan definitions
3. **Policy Management** – Issuance, endorsements, renewals, status
4. **Claims Management** – Full claims lifecycle
5. **Client Lifecycle Management** – Prospect → Policyholder → Renewal / Lapse
6. **Compliance Tracking** – Regulatory, audit, document control
7. **Automated Communications** – Reminders, status updates, multi-channel

## Recommended Additional Features.

### A. Quotation / Proposal Engine
- Generate personalized quotes from Scheme + client details (age, sum insured, members, loadings)
- Versioned proposals, convert to Policy with one click
- Comparison of multiple schemes side-by-side

### B. Premium Calculation Engine
- Central service / method that all modules call
- Supports age-band, sum-insured slabs, family floater, loadings (smoker, occupation), discounts (NCB, loyalty), taxes
- Audit log of every calculation

### C. Endorsement Management
- Dedicated DocType for mid-term changes (already outlined in Policy module)
- Financial impact calculation (additional / refund premium)
- Approval workflow

### D. Reinsurance (Basic)
- Facultative / Treaty tagging on large policies
- Cession percentage and recovery tracking on claims

### E. Commission & Agency Management
- Agent / Broker master (can extend Sales Partner or custom)
- Commission rules per scheme / provider
- Commission calculation on policy issue / renewal / collection
- Payout tracking

### F. TPA / Network Hospital Management
- Preferred provider network
- Cashless authorization workflow
- TPA-wise claim routing

### G. Document Generation
- Policy Schedule / Certificate PDF (Print Format + Jinja)
- Claim form, discharge voucher, settlement letter
- Use Frappe’s Print Format + optional wkhtmltopdf / WeasyPrint

### H. Portal / Customer Self-Service
- Web portal or desk page for clients to:
  - View policies & documents
  - Download policy copy
  - Intimate claim
  - Upload documents
  - Request endorsement
  - Pay premium (via payment gateway)

### I. Analytics & MIS
- Built-in reports + Insights dashboards (see Integration.md)
- Incurred Claim Ratio, Persistency, Average Premium, Channel performance

### J. Mobile / Offline Considerations
- Progressive Web App friendly forms
- Critical offline actions (claim intimation) if needed later

## Suggested App Structure
```
insurance_core/
├── insurance_core/
│   ├── doctype/
│   │   ├── insurance_provider/
│   │   ├── insurance_scheme/
│   │   ├── insurance_policy/
│   │   ├── policy_endorsement/
│   │   ├── insurance_claim/
│   │   ├── insurance_opportunity/
│   │   ├── compliance_document/
│   │   └── ...
│   ├── api/
│   ├── integrations/
│   │   ├── erpnext.py
│   │   ├── hrms.py
│   │   ├── crm.py
│   │   ├── helpdesk.py
│   │   └── healthcare.py
│   ├── public/
│   ├── templates/
│   ├── hooks.py
│   └── ...
├── docs/                
└── README.md
```

## Development Guidelines for Coding Agents
1. Follow Frappe coding standards (naming, permissions, documentation strings).
2. Every DocType must have clear `validate`, `before_submit`, `on_submit`, `on_cancel` methods.
3. Use `frappe.throw` with meaningful messages and title.
4. Write unit tests for premium calculation, status transitions, and accounting hooks.
5. Prefer Server Scripts / Client Scripts only for light customizations; core logic in Python controllers.
6. Make all Select options and workflows configurable via Insurance Settings where possible.
7. Internationalization: wrap all user-facing strings with `_()`.
8. Security: never expose sensitive medical / financial data in list views without permission checks.

## Settings DocType
Create **Insurance Settings** (Single) with:
- Default naming series
- Default accounts
- Grace period days
- Reminder days (30/15/7)
- Enable WhatsApp / SMS flags
- Integration toggles
- Compliance retention periods

## Next Steps for Agents
1. Implement masters first: Provider → Scheme
2. Then Policy + Member + Endorsement
3. Claims
4. Communications & Schedulers
5. Compliance & Checklists
6. Integrations one by one (start with ERPNext Customer + Accounting)
7. Portal & Print Formats
8. Reports & Insights dashboards
