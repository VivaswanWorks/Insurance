# Rename & Refactor Guide: Insurance Management → Insurance Core

## Goal
Resolve naming conflict with the existing **Healthcare** app (which already contains a sub-module / namespace called `insurance`).

**New official name:** **Insurance Core**

| Layer | Old (example) | New |
|-------|---------------|-----|
| App name (folder + `hooks.py`) | `insurance_management` / `insurance` | `insurance_core` |
| Module name (shown in Desk) | Insurance Management / Insurance | Insurance Core |
| Python package | `insurance_management` / `insurance` | `insurance_core` |
| Workspace | Insurance Management / `insurance` | Insurance Core |
| DocType name prefix (optional but recommended) | — | Keep clean names; avoid generic “Insurance” alone where conflict risk exists |
| Custom field / Property setter namespace | `insurance_management` / `insurance` | `insurance_core` |
| Print Format / Report / Notification names | containing old app name | Update to new |
| Site config / installed_apps | old name | `insurance_core` |

> **Important:** Never leave the app name as plain `insurance`. That will continue to clash with Healthcare’s internal `insurance` module.

---

## 1. High-level Steps (Order Matters)

1. Create a **new app** `insurance_core` (or rename in place carefully).
2. Move / copy all code, DocTypes, fixtures, public assets.
3. Rename Python package, imports, hooks, modules.
4. Rename Desk artefacts (Module Def, Workspace, Page, Report, Notification, Print Format, Web Form, etc.).
5. Update all DocType JSON (`module` field, naming series if needed, permissions).
6. Update links, Dynamic Links, client scripts, server scripts, custom scripts.
7. Update `hooks.py`, `modules.txt`, `patches.txt`, `fixtures`.
8. Write and run a **data migration patch** that updates `tabDocType.module`, `tabModule Def`, Workspace, etc.
9. Uninstall old app → Install new app (or use `bench migrate` after rename).
10. Search & replace remaining references (tests, documentation, README, CI).
11. Verify no remaining references to old name and no conflict with Healthcare.

---

## 2. App & Package Rename

### 2.1 Preferred approach (clean)
```bash
# From frappe-bench
bench new-app insurance_core
# Then copy code from old app into insurance_core/
# OR use git mv / careful filesystem rename
```

### 2.2 In-place rename (if already developed)
```bash
cd apps
mv insurance_management insurance_core
# or
mv insurance insurance_core
```

Then update:

**`insurance_core/hooks.py`**
```python
app_name = "insurance_core"
app_title = "Insurance Core"
app_publisher = "..."
app_description = "Core Insurance Management for Frappe / ERPNext"
app_email = "..."
app_license = "..."
app_version = "..."

# Update all references inside hooks
# doc_events, override_doctype_class, fixtures, scheduler_events, etc.
# Change every "insurance_management.xxx" → "insurance_core.xxx"
```

**`insurance_core/modules.txt`**
```
Insurance Core
```

**`insurance_core/patches.txt`**
- Keep existing patches; add a new patch for the rename (see section 6).

**Python package structure**
```
insurance_core/
├── insurance_core/
│   ├── __init__.py
│   ├── hooks.py
│   ├── modules.txt
│   ├── patches.txt
│   ├── insurance_core/          ← domain package (optional subfolder)
│   │   ├── doctype/
│   │   ├── api/
│   │   ├── eligibility/
│   │   ├── integrations/
│   │   └── ...
│   ├── public/
│   ├── templates/
│   └── config/
```

Update **every** import:
```python
# OLD
from insurance_management.insurance_management.doctype....
import insurance_management

# NEW
from insurance_core.insurance_core.doctype....
import insurance_core
```

---

## 3. Module Def & Workspace

### 3.1 Module Def
- Name: **Insurance Core**
- Module Name: `Insurance Core`
- App Name: `insurance_core`

If the old Module Def still exists, either:
- Rename it via patch, **or**
- Delete old and create new (then migrate DocTypes to the new module).

### 3.2 Workspace
- Rename Workspace title to **Insurance Core**
- Update `module` field to `Insurance Core`
- Update all shortcuts, charts, number cards that point to old module / DocTypes
- File location: `insurance_core/insurance_core/workspace/insurance_core/insurance_core.json` (or similar)

### 3.3 Desk Sidebar / Navbar
- Ensure the app appears as “Insurance Core”
- Icon / logo can stay or be updated

---

## 4. DocType Rename Strategy

### 4.1 Keep DocType names human-readable (recommended)
Do **not** prefix every DocType with “Insurance Core”.  
Keep:
- Insurance Provider
- Insurance Scheme
- Insurance Policy
- Insurance Claim
- Client Eligibility Criteria
- etc.

**Why?**  
- Users already understand these names.
- Changing DocType names is a breaking change (all Link fields, reports, custom scripts break).

### 4.2 What must change inside every DocType JSON
```json
{
  "name": "Insurance Policy",
  "module": "Insurance Core",          ← CHANGE THIS
  "naming_rule": "...",
  ...
}
```

Also update:
- `permissions` (if role names changed)
- `links` / `actions`
- any hard-coded old app references in `description` or help text

### 4.3 Child DocTypes & custom tables
Same rule – only change the `module` field to `Insurance Core`.

### 4.4 Naming Series (optional cleanup)
If any naming series contained the old app abbreviation, update via patch:
```python
# Example
frappe.db.sql("""
    UPDATE `tabSeries` SET name = REPLACE(name, 'IM-', 'IC-')
    WHERE name LIKE 'IM-%'
""")
```
Document the new series in Insurance Settings.

---

## 5. Other Desk Artefacts to Rename / Update

| Artefact | Action |
|----------|--------|
| **Print Format** | Update `module` + any Jinja that imported old paths |
| **Report** (Query / Script / Report Builder) | `module` = Insurance Core; update SQL / script if needed |
| **Notification** | `module` + document_type still points to correct DocType |
| **Client Script / Server Script** | Update module; rewrite any `frappe.call` to new dotted paths |
| **Web Form** | module + login requirements |
| **Page / Custom HTML Page** | module |
| **Dashboard / Dashboard Chart / Number Card** | module + document_type |
| **Workflow** | document_type stays same; only module if stored |
| **Custom Field** | `module` = Insurance Core (or leave empty) |
| **Property Setter** | update `module` / `doc_type` if necessary |
| **Translation / __`** | no change needed if strings are clean |
| **Fixtures** | regenerate after rename (`bench export-fixtures`) |

---


## 6. Verification Checklist for Agents

- [ ] `bench list-apps` shows `insurance_core`
- [ ] Desk → Module dropdown shows **Insurance Core** (not “Insurance”)
- [ ] No Module Def named exactly “Insurance” left by this app
- [ ] All DocTypes have `module = "Insurance Core"`
- [ ] Workspace opens without error and shows correct shortcuts
- [ ] Creating a new Insurance Policy / Claim works
- [ ] Eligibility engine still runs (import paths updated)
- [ ] Accounting / HRMS / Healthcare integrations still fire
- [ ] `rg insurance_management` returns zero hits inside the app
- [ ] Healthcare app continues to work (its own insurance sub-module untouched)
- [ ] Permissions / roles still assigned correctly
- [ ] Print Formats and Reports render
- [ ] Scheduler jobs appear under “Insurance Core” or correct dotted paths

---

## 7. Recommended Final Naming Convention

| Item | Convention |
|------|------------|
| App folder / package | `insurance_core` |
| App title | Insurance Core |
| Module Def | Insurance Core |
| Workspace | Insurance Core |
| DocTypes | Insurance Provider, Insurance Scheme, Insurance Policy, Insurance Claim, Client Eligibility Criteria, … |
| Python modules | `insurance_core.doctype.xxx`, `insurance_core.eligibility`, `insurance_core.integrations` |
| Naming series | `IC-POL-.YYYY.-`, `IC-CLM-.YYYY.-`, `IC-SCH-.YYYY.-` etc. (optional cleanup) |
| Roles | Insurance Manager, Insurance User, Claims Assessor (unchanged) |
| Custom fields on other apps | `module = "Insurance Core"` |

---

## Summary for Coding Agents

1. **Never** use the bare name `insurance` for the app or module.
2. Target name is **`insurance_core`** (code) / **Insurance Core** (UI).
3. Prefer changing only the `module` field on DocTypes rather than renaming the DocTypes themselves.
4. Always ship a migration patch that moves existing data to the new module.
5. After rename, perform a full-text search for the old name and eliminate every reference.
6. Confirm coexistence with Healthcare by installing both apps on a clean site and running smoke tests.
