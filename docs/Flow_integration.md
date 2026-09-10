# Flow Integration — AI Claim Triage

This guide covers installing [Frappe Flow](https://github.com/frappe/flow_client), configuring a model/provider, wiring the **Claim Triage Agent**, and using AI triage on **Insurance Claim**.

Insurance Core combines:

1. **Deterministic eligibility** (`insurance_core.eligibility`) — Claim Success Score, mandatory gates, evaluation log.
2. **LLM judgment** (Flow Agent) — compares claim narrative, documents, and guidelines; recommends **process**, **reject**, or **pending**.

---

## Prerequisites

- Frappe bench with `insurance_core` installed and migrated.
- Network access to an LLM provider (Anthropic, OpenAI, or a local endpoint such as Ollama / LM Studio).
- Roles: **System Manager** or **Insurance Manager** for setup; Claims Adjuster / Insurance User can run triage.

---

## 1. Install Flow

From your bench:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app flow
# Official app may also appear as flow_client depending on the clone URL:
# bench get-app https://github.com/frappe/flow_client.git
bench --site <site-name> install-app flow
bench --site <site-name> migrate
bench restart
```

Confirm DocTypes exist: **Flow Provider**, **Flow Model**, **Flow Tool**, **Flow Agent**, **Flow Trigger**, **Flow Run**.

---

## 2. Configure provider and model

### Flow Provider

1. Open **Flow Provider** → New.
2. Set provider credentials (API key) and endpoint if required.
3. For local models (Ollama, LM Studio), set **Base URL** on the provider or model.

### Flow Model

1. Open **Flow Model** → New.
2. Link the provider.
3. Set `model_id`, for example:
   - `anthropic/claude-sonnet-4-6`
   - `openai/gpt-4o`
   - A local model id supported by your provider
4. Enable the model.

You need at least one **enabled** Flow Model before the Claim Triage Agent can be created.

---

## 3. Wire Insurance Core triage (one-time)

### Option A — Desk button (recommended)

1. Open any **Insurance Claim** form (existing record).
2. Menu **AI** → **Setup Flow Agent**.
3. Review the JSON result: tools created, agent name, trigger name.

This calls `insurance_core.ai_triage.setup_claim_ai_triage` and is idempotent.

### Option B — Migrate / console

On migrate, `insurance_core.install.after_migrate` calls `setup_ai_triage()` when Flow is present.

Or in `bench console`:

```python
from insurance_core.ai_triage import ensure_flow_triage_setup
print(ensure_flow_triage_setup())
```

### What gets created

| Object | Name / slug | Purpose |
|--------|-------------|---------|
| Flow Tool | `get_claim_eligibility` | Deterministic score + criteria results |
| Flow Tool | `get_claim_context` | Claim, policy, client, scheme, documents |
| Flow Tool | `apply_triage_decision` | Apply process / reject / pending |
| Flow Agent | **Claim Triage Agent** | Instructions + tools + model |
| Flow Trigger | **Claim AI Triage on Submit/Update** | Optional auto-run on claim update (created **disabled**) |
| Custom fields on Insurance Claim | `ai_success_probability`, `ai_recommended_action`, `ai_triage_at`, `ai_suggestion_document` | Persist last triage |

Import paths for tools:

- `insurance_core.ai_triage.get_claim_eligibility`
- `insurance_core.ai_triage.get_claim_context`
- `insurance_core.ai_triage.apply_triage_decision`

---

## 4. Decision rules

| Condition | Recommended action | Status (when apply is on) |
|-----------|--------------------|---------------------------|
| Success probability ≥ **80%** and no hard mandatory failures | **process** | Under Review |
| Success probability ≤ **40%** **or** mandatory eligibility failures | **reject** | Rejected (+ rejection reason) |
| Otherwise | **pending** | Additional Info Required + suggestion file |

Thresholds are constants in `insurance_core.ai_triage` (`HIGH_PROBABILITY = 80`, `LOW_PROBABILITY = 40`). Mandatory eligibility failures always block a pure “process” outcome.

The agent **never** marks a claim Settled or sets final approved payout amounts — humans retain settlement authority.

---

## 5. Usage on Insurance Claim

### Advisory only (no status change)

**AI → AI Triage (advisory only)**

- Runs eligibility + Flow agent.
- Writes AI fields and assessment notes.
- Does **not** change `status`.
- Use this first while validating prompts and model quality.

### Apply triage

**AI → AI Triage**

- Same as above, then applies status change when the claim is in:
  - Draft, Submitted, Under Review, Documents Pending, Additional Info Required
- **pending** also attaches a private **File** (suggestion document) listing missing items and improvements.

### Optional automatic trigger

1. Open **Flow Trigger** → **Claim AI Triage on Submit/Update**.
2. Review condition (status in Submitted / Under Review / Documents Pending / Additional Info Required).
3. Set **Auto Approve Tool Calls** if you want unattended runs.
4. **Enable** the trigger when ready.

Start with the button; enable the trigger only after you trust the model and instructions.

---

## 6. API reference

```python
# Full triage (button path)
frappe.call(
    "insurance_core.ai_triage.run_claim_ai_triage",
    claim_name="CLM-2026-00001",
    apply_status_change=1,  # 0 = advisory
)

# Setup only
frappe.call("insurance_core.ai_triage.setup_claim_ai_triage")

# Tools (also callable by the Flow agent)
from insurance_core.ai_triage import (
    get_claim_eligibility,
    get_claim_context,
    apply_triage_decision,
)
```

Return shape of `run_claim_ai_triage`:

```json
{
  "decision": {
    "success_probability": 72,
    "recommended_action": "pending",
    "reasons": "...",
    "missing_items": "...",
    "suggested_improvements": "..."
  },
  "apply": {
    "status_changed_to": "Additional Info Required",
    "suggestion_document": "File-..."
  },
  "eligibility": {
    "overall_score": 65,
    "overall_status": "Conditionally Eligible",
    "can_submit": true,
    "failed_mandatory": []
  }
}
```

---

## 7. Knowledge bases (optional)

To ground the agent in scheme wordings and SOPs:

1. Create a **Flow Knowledge Base**.
2. Add **Flow Knowledge Source** rows (files, URLs, or DocTypes such as Insurance Scheme).
3. Attach the knowledge base to **Claim Triage Agent** → Knowledge Bases.

Useful sources: policy wordings, exclusion lists, claims SOP PDFs, historical Claim Eligibility Evaluation outcomes (for calibration).

---

## 8. Troubleshooting

| Symptom | What to check |
|---------|----------------|
| “Frappe Flow is not installed” | `bench list-apps`; install `flow` and migrate |
| “No Flow Model configured” | Create/enable Flow Provider + Flow Model |
| Setup returns tools but no agent | Model missing; re-run Setup after adding a model |
| Agent runs but no status change | Use **AI Triage** (not advisory); claim status may be outside the allowed set |
| Mandatory failures still “process” | Code forces reject when `failed_mandatory` is non-empty |
| Trigger never fires | Trigger still disabled; condition or server-script sandbox for conditions |
| Import path errors on tools | Ensure `insurance_core.ai_triage` is on the site and migrated |

Fallback: if the Flow agent cannot run, triage still applies a **deterministic** decision from the eligibility score so the Desk button remains usable offline.

---

## 9. Security and audit

- Tool calls respect Frappe permissions of the running user (or **Run As** on the trigger).
- Every Flow execution is stored as **Flow Run** / **Flow Session**.
- Claim changes are written to `assessment_notes`, AI fields, optional **Claim Assessment Log**, and suggestion **File**.
- Prefer a least-privilege service user on the trigger rather than Administrator.

---

## 10. Related code

| Path | Role |
|------|------|
| `insurance_core/ai_triage.py` | Tools, `run_claim_ai_triage`, `ensure_flow_triage_setup` |
| `insurance_core/eligibility.py` | Deterministic Claim Success Score |
| `insurance_core/install.py` | `setup_ai_triage()` on install/migrate |
| Claim form JS | **AI** button group |

Upstream Flow documentation: [github.com/frappe/flow_client](https://github.com/frappe/flow_client).
