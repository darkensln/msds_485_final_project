# FinGuard Week 10 — Live Demo Runbook

A five-minute walkthrough that exercises all four Week 10 deliverables
end-to-end. Aligned with slide 15 of `FinGuard_Week10_Final.pptx`.

## Pre-demo checklist

1. Backend running on `:8000` (`uvicorn app.main:app --reload --port 8000`).
2. Frontend running on `:5173` (`npm run dev`).
3. Hit <http://localhost:8000/api/health> — verify `ok: true` and
   `catalog_columns: 98`.
4. Open <http://localhost:5173>. The role switcher should default to
   **Data Analyst** (masked).

## Five-minute live flow

### 1. Open the Data Catalog (Deliverable B) — 60 sec

- Land on the **Data Catalog** tab.
- Walk through the five KPI tiles: 7 tables, 98 columns, 26 PII, 24 masked, 28 DQ flags.
- Toggle **PII only** filter → only 26 rows. Click the **DQ issues** filter on top → narrower set.
- Search `email` → multiple tables surface (`customer_email`, `email`).
- Click **Details →** on `aml_transactions.customer_email`.

### 2. Inspect a column + role-aware sample — 60 sec

- The detail page shows: Restricted classification, Direct PII, SHA-256 mask,
  steward, retention period, GDPR Art. 4(1) reference, DQ status, lineage.
- Sample table at the bottom shows masked emails for the Data Analyst role.
- Switch role to **Data Privacy Officer** in the header dropdown — sample row
  reloads with **raw** emails. Switch back to **Data Analyst**; masked again.

> Talking point: *"This is the same row in the same database. The catalog
> doesn't gate access at view time — it shows what each role is *allowed*
> to see, enforced by the backend, logged on every call."*

### 3. Open the Lineage tab (Deliverable A) — 45 sec

- **System view** by default: External → Raw → Privacy → Consumption →
  Consumers. Show the Vault as the privacy-layer endpoint.
- Switch to **Column-level**, filter to `aml_transactions` — show every PII
  column's hop from source to masking method to masked destination to
  consuming roles.

### 4. Compliance Dashboard (Deliverable C) — 60 sec

- KPI tiles: 24/24 PII masked, 28,893 vault entries, 4+ erasures processed,
  29 RBAC denials, 12 active SARs, 96.2 % quality-gate pass rate.
- Charts: classification doughnut + PII-by-type bar.
- Regulators-satisfied ribbon: GDPR, GLBA, PSD2, EU AI Act, CCPA, EU AMLD.
- Audit log + erasure history at the bottom.

### 5. GDPR erasure workflow (Deliverable D) — 60 sec

- Switch role to **Data Analyst** → open the **GDPR Erasure** tab. Submit
  button is disabled with a red warning banner.
- Switch role to **DPO**. Submit an erasure for `CUST-00099` with the
  default reason → success card appears, listing impacted tables.
- Back to **Compliance Dashboard** → erasure now appears in the history,
  and an `ERASURE` entry is at the top of the audit log.

### 6. (Optional) Show the deck — 30 sec

- Open `FinGuard_Week10_Final.pptx` → slide 9 (Week 10 overview) and slide
  18 (closing pitch) for the storyline.

## Anticipated questions (with crisp answers)

**Q: Why these masking methods specifically?**
A: We match the *use case* of the field. Names/IDs → pseudonymization so
joins still work for AML. Emails → SHA-256 because we never need them back
for analytics. Phones → partial masking for customer-service confirmation.
IBANs/EINs → format-preserving encryption so downstream validators don't
break. Slide 6 lists all seven.

**Q: How does the reversible vault avoid being the next breach?**
A: AES-256 at rest; access restricted to CDO and DPO only; mappings are
stored in a JSON vault separate from analytics warehouses; every unlock
is recorded in the audit log; entries are pruned when GDPR erasure fires.

**Q: What happens end-to-end when a customer asks to be forgotten?**
A: Slide 14: customer → DPO authenticates → cascade lookup across every
table containing the customer_id → vault entries removed (so masked values
can never be reversed again) → audit log records actor, timestamp, impact
→ confirmation within the 72-hour GDPR window.

**Q: How does the AML model avoid proxy discrimination under EU AI Act?**
A: We treat the model as high-risk under the Act: explicit human oversight
(AML Officer), bias-sensitive features (age, country) tagged in the
catalog, decisions logged to the audit table for review, and the model is
quarantined from raw PII via masked views.

## Backup plan if anything fails live

A pre-recorded 90-second walkthrough of each tab is on the demo laptop's
Desktop. Slide 15 of the deck mirrors this runbook so you can narrate
through screenshots if the live app refuses to start.
