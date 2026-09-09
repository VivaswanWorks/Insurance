# Automated Communications Module

## Purpose
Trigger timely, personalized, multi-channel communications (Email, SMS, WhatsApp, In-app, Push) for policy lifecycle events, claims updates, renewals, premium dues, and compliance notices.

## Architecture
Prefer Frappe’s built-in Notification + Email Queue + SMS Settings.
Extend with:
- WhatsApp (via Twilio / Gupshup / Interakt or Frappe WhatsApp app)
- Custom Notification Channel if needed

## Event-Driven Notifications

### Policy Lifecycle
| Event | Trigger | Recipients | Channels | Template Key |
|-------|---------|------------|----------|--------------|
| Policy Issued | on_submit of Insurance Policy | Client, Agent | Email, SMS, WhatsApp | policy_issued |
| Policy Expiring | Daily scheduler (30/15/7 days before end_date) | Client, Agent | Email, SMS, WhatsApp | policy_expiring |
| Premium Due | Daily scheduler | Client | Email, SMS | premium_due |
| Premium Overdue | Daily scheduler | Client, Collections | Email, SMS | premium_overdue |
| Policy Renewed | on_submit of Renewal Policy | Client | Email, WhatsApp | policy_renewed |
| Policy Lapsed / Cancelled | Status change | Client | Email | policy_lapsed |

### Claims Lifecycle
| Event | Trigger | Recipients | Channels | Template Key |
|-------|---------|------------|----------|--------------|
| Claim Submitted | on_submit | Client, Claims Team | Email | claim_submitted |
| Additional Info Required | Status change | Client | Email, SMS | claim_info_required |
| Claim Approved | Status change | Client | Email, WhatsApp | claim_approved |
| Claim Rejected | Status change | Client | Email | claim_rejected |
| Claim Settled | Settlement | Client, Finance | Email | claim_settled |

### Other
- Birthday / Anniversary wishes (optional)
- KYC expiring
- New scheme launch (marketing – opt-in only)
- Grievance acknowledgement & resolution

## Implementation Guidelines for Agents

1. **Create Email Templates** (Email Template DocType) for each key above.
   - Use Jinja: `{{ doc.policy_number }}`, `{{ doc.client_name }}`, `{{ doc.end_date }}`, etc.
2. **Create Notification records** (Notification DocType) linked to the events.
   - Channel: Email / SMS
   - Condition: Python expression if needed
3. **Custom Scheduler** (`hooks.py` → `scheduler_events`):
   ```python
   "daily": [
       "insurance_core.insurance_core.doctype.insurance_policy.insurance_policy.send_expiry_reminders",
       "insurance_core.insurance_core.doctype.insurance_policy.insurance_policy.send_premium_reminders"
   ]
   ```
4. **WhatsApp Integration**:
   - Prefer existing Frappe WhatsApp app or custom API wrapper.
   - Store templates in a custom DocType `WhatsApp Template` mapped to events.
5. **Preference Management**:
   - On Customer / Contact: fields for Email Opt-in, SMS Opt-in, WhatsApp Opt-in
   - Respect preferences before sending
6. **Communication Log**:
   - Every automated message should create a Communication record linked to the Policy / Claim / Client for full audit trail.
7. **Rate Limiting & Quiet Hours**:
   - Configurable quiet hours (e.g. no SMS 9 PM – 8 AM)
   - Deduplication: do not send same reminder more than once per day

## Testing Checklist for Agents
- [ ] Template renders correctly with sample data
- [ ] Notification fires on correct event
- [ ] Opt-out is respected
- [ ] Communication record is created
- [ ] Multi-language support (if required) via Language field
- [ ] Failure handling (email bounce → mark status)

## Permissions
- System Manager / Insurance Manager: manage templates & notifications
- Users: only view communication history on documents they can read
