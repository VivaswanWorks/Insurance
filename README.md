# Insurance Core – Overview & Features

## Core Modules
1. **Insurance Provider** – Master data for insurers, TPAs, brokers
2. **Insurance Scheme** – Product / plan definitions
3. **Policy Management** – Issuance, endorsements, renewals, status
4. **Claims Management** – Full claims lifecycle
5. **Client Lifecycle Management** – Prospect → Policyholder → Renewal / Lapse
6. **Compliance Tracking** – Regulatory, audit, document control
7. **Automated Communications** – Reminders, status updates, multi-channel

## Additional Features

### A. Quotation / Proposal Engine
- Generate personalized quotes from Scheme + client details (age, sum insured, members, loadings)
- Versioned proposals, convert to Policy with one click
- Comparison of multiple schemes side-by-side

### B. Premium Calculation Engine
- Central service / method that all modules call (`insurance_core.premium.calculate_premium`)
- Supports age-band, sum-insured slabs, family floater, loadings, discounts, taxes
- Audit log of every calculation (`Premium Calculation Log`)

### C. Endorsement Management
- DocType **Policy Endorsement** with workflow: Draft → Submitted → Approved → Applied / Rejected
- Types: Member Addition/Deletion, Sum Insured Change, Address Change, Nominee Change, Correction, Cancellation
- Auto estimate of premium impact; apply updates the parent policy
- Desk buttons: Approve, Reject, Apply, Estimate Premium Impact
- Portal: clients can request endorsements from policy detail

### D. Reinsurance (Basic)
- Facultative / Treaty tagging on policies
- Cession percentage and recovery tracking on claims

### E. Commission & Agency Management
- **Commission Rule** (scheme / provider / event + rate and/or fixed amount)
- Auto accrual of **Commission Payout**:
  - **Issue / Renewal** when policy becomes Active
  - **Collection** when `payment_status` becomes Paid
  - Positive premium impact on applied endorsements
- Approve → Mark Paid workflow; Agent Commission summary API

### F. TPA / Network Hospital Management
- Preferred provider network
- Cashless authorization workflow
- TPA-wise claim routing

### G. Document Generation
- Jinja templates under `insurance_core/templates/print_formats/`:
  - Policy Schedule
  - Claim Form
  - Settlement Letter
- API: `insurance_core.api.get_print_html` / portal download

### H. Portal / Customer Self-Service
- Vue SPA at `/insurance_core` (shared nav: Dashboard, Policies, Claims, New Claim)
- Dashboard, policies list/detail, claim intimation, endorsement request
- Download policy schedule; download settlement letter for settled claims
- API module: `insurance_core.portal` (scoped by client email ↔ logged-in user)

### I. Analytics & MIS
- Agent Commission summary
- Further Insights dashboards planned (see `specs/08_Integration.md`)

## Installation

This repository is a Frappe app. Place it under `frappe-bench/apps/insurance_core`, then:

```bash
# Install the app on a site
bench --site <site> install-app insurance_core

# Build the Vue SPA (from the app root)
cd frontend
yarn
yarn build
```

Dev server:

```bash
cd frontend
yarn dev
```

SPA route: `/insurance_core`. Built assets: `/assets/insurance_core/frontend/`.

## Usage

### Endorsements (Desk)
1. Create **Policy Endorsement** linked to a policy.
2. Optionally click **Estimate Premium Impact**.
3. **Approve** (Insurance Manager), then **Apply to Policy**.

### Commissions
1. Define **Commission Rule** rows (event Issue / Renewal / Collection; rate and/or fixed amount).
2. Ensure the policy `agent` matches an **Insurance Agent** (code or name).
3. When policy status becomes **Active**, a **Commission Payout** is accrued (Issue/Renewal).
4. When `payment_status` becomes **Paid**, a Collection payout is accrued.
5. Approve and Mark Paid from the payout form.

### Print formats
```python
frappe.call("insurance_core.api.get_print_html", doctype="Insurance Policy", name="POL-…")
frappe.call("insurance_core.api.get_print_html", doctype="Insurance Claim", name="CLM-…", template_key="claim_settlement")
```

### Customer portal
1. Link the client’s email to a Frappe User.
2. Open `/insurance_core` while logged in as that user.
3. View policies, download schedule, intimate claims, request endorsements, download settlement letters.

## Resources

- [Vue 3](https://v3.vuejs.org/guide/introduction.html)
- [Vue Router](https://next.router.vuejs.org/guide/)
- [Frappe UI](https://github.com/frappe/frappe-ui)
- [TailwindCSS](https://tailwindcss.com/docs/utility-first)
- [Vite](https://vitejs.dev/guide/)
