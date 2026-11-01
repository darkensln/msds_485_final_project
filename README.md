# FinGuard — Borderless Banking: Data Governance, Privacy & Compliance

**Course:** MSDS 485 — Data Governance, Ethics & Law · Northwestern University (Spring 2026)
**Team:** Selin Altiparmak · Yang Yu · Lixuan Xiao

FinGuard is a (fictional) US fintech launching banking services in the EU. To get a license it has to
prove to regulators that European customers' data is classified, masked, access-controlled, erasable on
request (GDPR Art. 17) and used fairly. This repo is the full 10-week governance build, ending in a
working web console.

## The live console (Week 10)

`finguard_week10/` is a FastAPI + React app with five tabs:

| Tab | What it shows |
|---|---|
| **Data Catalog** | Search 98 columns across 7 tables; classification, PII type, masking method, steward, retention, data-quality flags |
| **Lineage** | System-level and column-level lineage graph: source → masking → vault → consumers |
| **Compliance Dashboard** | Masking coverage, live vault stats, audit log, RBAC denials, erasure history |
| **GDPR Erasure** | Art. 17 workflow — DPO/CDO only, cascades across tables, shreds vault entries, refuses duplicates |
| **AI Ethics (UNESCO)** | 10 UNESCO principles mapped to 30 concrete FinGuard controls |

**What's enforced, not just described**

- **Role-based masking** — 7 roles; the same row returns raw PII for the DPO/CDO and masked values
  (pseudonyms, hashes, partial masks, decade age bands, truncated ZIP/IP) for everyone else. Every read and
  denial is written to the audit log.
- **AES-256-GCM vault** — reversible tokens are encrypted; only DPO/CDO can detokenize (analyst → HTTP 403).
- **GDPR Art. 17 erasure** — deletes the customer's vault entries so their tokens can never be reversed again;
  a second request for the same customer is refused.

**Run it:** see [`finguard_week10/README.md`](finguard_week10/README.md) — one setup command, one start command
(Mac/Linux `.sh` or Windows `.cmd`).

## Weekly deliverables → where to find them

| Week | Deliverable | Location |
|---|---|---|
| 1–3 | Use case, proposal, source datasets | 7 raw CSVs in the repo root (synthetic; 33,197 rows) |
| 4–5 | EDA, data-quality issues, 3NF models | Data-quality flags per column in `finguard_week10/data/FinGuard_Data_Catalog.xlsx` |
| 6 | PII identification & masking | `FinGuard Week6 Masked Data 3.zip` (masked CSVs + reverse mapping) |
| 7 | Classification, RACI, RBAC | `FinGuard_Week7_RACI_RBAC (1).xlsx`, `finguard_rbac_implementation.sql` (PostgreSQL roles, grants, row-level security) |
| 8 | Data bias (ethics & law) | [`finguard_week10/week8_fairness_audit.ipynb`](finguard_week10/week8_fairness_audit.ipynb) — four-fifths rule + significance tests |
| 9 | Data lineage | Console → Lineage tab (`backend/app/lineage.py`) |
| 10 | Catalog web UI + final presentation | `finguard_week10/`, `FinGuard_Week10_Final.pptx`, `FinGuard_Recap.pptx` |

## Week 8 fairness results (computed)

| Check | Lowest impact ratio | Chi-square p | Disparate impact? |
|---|---|---|---|
| AML flags · FATF grey/black-listed vs. other countries | 0.997 | 0.80 | No |
| AML flags · age band | 0.964 | 0.74 | No |
| Marketing subscription · age band | 0.478 (10s, n=97) | 0.73 | No — below 0.80 on ratio but not significant; monitor |
| Marketing subscription · marital status | 0.807 | 0.12 | No |
| Marketing subscription · education | 0.812 | 0.43 | No |

Re-run the notebook to reproduce. These computed results supersede the illustrative Week 8 figures on
slide 9 of `FinGuard_Recap.pptx`.

## Notes

- All data is **synthetic** — no real customers.
- Demo state (audit log, erasures, vault) is in memory and resets on restart; 4 historical erasures and
  180 audit entries are seeded so the dashboard isn't empty. "Active SARs" and "quality-gate pass rate" are
  illustrative values and are labelled as such in the UI.
- GDPR timing: erasure requests must be answered within **one month** (Art. 12(3)); **72 hours** is the
  breach-notification deadline (Art. 33).
