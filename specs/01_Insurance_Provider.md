# Insurance Provider Module

## Purpose
Central master data for all insurance companies / underwriters that the organization deals with (own company, partner insurers, reinsurers, TPAs, brokers).

## DocType: Insurance Provider

### Naming
- Naming Series: `IP-.YYYY.-.#####`
- Title Field: `provider_name`

### Fields

| Fieldname | Label | Type | Options / Details | Mandatory | Description |
|-----------|-------|------|-------------------|-----------|-------------|
| provider_name | Provider Name | Data | | Yes | Legal name of the insurance company |
| provider_code | Provider Code | Data | Unique | Yes | Short unique code (e.g. HDFC_ERGO) |
| provider_type | Provider Type | Select | Own Company, Partner Insurer, Reinsurer, TPA, Broker, Aggregator | Yes | |
| status | Status | Select | Active, Inactive, Suspended | Yes | Default: Active |
| is_group | Is Group | Check | | | For hierarchical providers |
| parent_provider | Parent Provider | Link | Insurance Provider | | If is_group = 0 |
| logo | Logo | Attach Image | | | |
| website | Website | Data | | | |
| registration_number | IRDAI / Regulator Registration No. | Data | | | |
| license_valid_upto | License Valid Upto | Date | | | |
| gstin | GSTIN | Data | | | |
| pan | PAN | Data | | | |
| cin | CIN | Data | | | |

#### Address & Contact (use standard Child Tables)
- Use `Address` and `Contact` DocTypes via Dynamic Link / standard ERPNext pattern.
- Child Table: `provider_addresses` → Link to Address
- Child Table: `provider_contacts` → Link to Contact

#### Financial & Settlement
| Fieldname | Label | Type | Options | Mandatory |
|-----------|-------|------|---------|-----------|
| default_currency | Default Currency | Link | Currency | Yes |
| payment_terms | Payment Terms | Link | Payment Terms Template | |
| bank_account | Bank Account | Link | Bank Account | |
| settlement_cycle | Settlement Cycle | Select | Daily, Weekly, Monthly, Quarterly | |
| commission_payable | Commission Payable Account | Link | Account | |
| claims_payable | Claims Payable Account | Link | Account | |
| premium_receivable | Premium Receivable Account | Link | Account | |

#### Compliance & Documents
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| agreement_start | Agreement Start Date | Date | |
| agreement_end | Agreement End Date | Date | |
| documents | Documents | Table | Insurance Provider Document |
| remarks | Remarks | Text Editor | |

### Child DocType: Insurance Provider Document
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| document_type | Document Type | Select | Agreement, License, MOU, Rate Sheet, Other |
| document_name | Document Name | Data | |
| attachment | Attachment | Attach | |
| valid_from | Valid From | Date | |
| valid_upto | Valid Upto | Date | |
| notes | Notes | Small Text | |

### Permissions
- Insurance Manager: Full
- Insurance User: Read + Write (limited)
- System Manager: Full

### List View / Kanban
- Filters: Status, Provider Type
- Quick filters: Active only

### Scripts / Logic
- Validate unique `provider_code`
- On save: if `license_valid_upto` < today → set status = Suspended (with warning)
- Dashboard: count of active schemes, total policies, outstanding claims

### API / Hooks
- `get_active_providers()` – returns list of Active providers
- Hook: `on_update` → update linked schemes if provider becomes Inactive
