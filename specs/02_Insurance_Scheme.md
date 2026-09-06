# Insurance Scheme Module

## Purpose
Define the actual insurance products / plans offered by providers (e.g. Group Mediclaim, Term Life, Motor Comprehensive, Property All Risk).

## DocType: Insurance Scheme

### Naming
- Naming Series: `SCH-.YYYY.-.#####`
- Title Field: `scheme_name`

### Fields

| Fieldname | Label | Type | Options / Details | Mandatory |
|-----------|-------|------|-------------------|-----------|
| scheme_name | Scheme Name | Data | | Yes |
| scheme_code | Scheme Code | Data | Unique | Yes |
| insurance_provider | Insurance Provider | Link | Insurance Provider | Yes |
| scheme_type | Scheme Type | Select | Life, Health, Motor, Property, Liability, Travel, Cyber, Marine, Other | Yes |
| product_category | Product Category | Select | Individual, Group, Corporate, Retail | Yes |
| status | Status | Select | Draft, Active, Inactive, Discontinued | Yes | Default: Draft |
| description | Description | Text Editor | | |
| brochure | Brochure / Product Note | Attach | | |

#### Coverage & Benefits
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| coverage_type | Coverage Type | Select | Fixed Benefit, Indemnity, Hybrid |
| sum_insured_type | Sum Insured Type | Select | Fixed, Floater, Per Member, Per Policy |
| min_sum_insured | Minimum Sum Insured | Currency | |
| max_sum_insured | Maximum Sum Insured | Currency | |
| currency | Currency | Link | Currency | Default: Company currency |
| waiting_period_days | Waiting Period (Days) | Int | |
| pre_existing_waiting | Pre-existing Disease Waiting (Days) | Int | |
| coverage_details | Coverage Details | Table | Scheme Coverage Item |
| exclusions | Exclusions | Table | Scheme Exclusion |
| benefits | Key Benefits | Table | Scheme Benefit |

### Child: Scheme Coverage Item
| Fieldname | Label | Type |
|-----------|-------|------|
| coverage_name | Coverage / Benefit Name | Data |
| description | Description | Small Text |
| is_mandatory | Mandatory | Check |
| max_limit | Max Limit | Currency |
| percentage | % of Sum Insured | Percent |
| notes | Notes | Small Text |

### Child: Scheme Exclusion
| Fieldname | Label | Type |
|-----------|-------|------|
| exclusion | Exclusion | Data |
| description | Description | Small Text |

### Child: Scheme Benefit
| Fieldname | Label | Type |
|-----------|-------|------|
| benefit | Benefit | Data |
| description | Description | Small Text |
| value | Value / Limit | Data |

#### Premium Structure
| Fieldname | Label | Type | Options |
|-----------|-------|------|---------|
| premium_basis | Premium Basis | Select | Age Band, Sum Insured, Flat, Per Member, Salary %, Custom |
| premium_table | Premium Table | Table | Scheme Premium Slab |
| loading_discount_rules | Loading / Discount Rules | Table | Scheme Loading Discount |
| gst_applicable | GST Applicable | Check | Default: 1 |
| gst_rate | GST Rate | Percent | |

### Child: Scheme Premium Slab
| Fieldname | Label | Type |
|-----------|-------|------|
| age_from | Age From | Int |
| age_to | Age To | Int |
| sum_insured_from | Sum Insured From | Currency |
| sum_insured_to | Sum Insured To | Currency |
| premium_amount | Premium Amount | Currency |
| premium_rate | Premium Rate (%) | Percent |
| frequency | Frequency | Select: Monthly, Quarterly, Half-Yearly, Yearly |

### Child: Scheme Loading Discount
| Fieldname | Label | Type |
|-----------|-------|------|
| rule_type | Rule Type | Select: Loading, Discount |
| criteria | Criteria | Data (e.g. "Smoker", "No Claim Bonus") |
| percentage | Percentage | Percent |
| amount | Fixed Amount | Currency |
| applicable_on | Applicable On | Select: Premium, Sum Insured |

#### Terms & Conditions
| Fieldname | Label | Type |
|-----------|-------|------|
| policy_term_months | Default Policy Term (Months) | Int | Default: 12 |
| renewal_allowed | Renewal Allowed | Check | Default: 1 |
| max_renewals | Max Renewals | Int |
| grace_period_days | Grace Period (Days) | Int | Default: 30 |
| terms_and_conditions | Terms & Conditions | Text Editor |
| claim_process | Claim Process Overview | Text Editor |

### Permissions
- Insurance Manager: Full
- Insurance User: Read + limited Write
- System Manager: Full

### Business Logic
- Only Active schemes can be selected in Policy
- When Provider becomes Inactive → cascade warning / auto-inactivate schemes
- Method: `calculate_premium(age, sum_insured, members, extras)` → returns premium breakdown

### API
- `get_schemes_by_provider(provider)`
- `get_active_schemes(scheme_type=None)`
- `calculate_premium(scheme, params)`
