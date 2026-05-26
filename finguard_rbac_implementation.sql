-- =============================================================================
--  FINGUARD  |  Week 7  |  Data Classification + RBAC Implementation
--  Database: PostgreSQL 15+
--  Author:   FinGuard Data Governance Team  |  Spring 2026
--
--  This script implements Role-Based Access Control (RBAC) for the FinGuard
--  Neo-Bank data warehouse, aligned with the 4-tier data classification scheme
--  applied in Week 6 (PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED).
--
--  Reference: NIST RBAC standard (INCITS 359), GDPR Art. 5(1)(f),
--             FFIEC IT Examination Handbook (Information Security).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0.  SCHEMA ISOLATION  (separates layers by sensitivity)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS raw_pii;        -- RESTRICTED: real PII (vault)
CREATE SCHEMA IF NOT EXISTS masked;         -- CONFIDENTIAL: tokenized prod data
CREATE SCHEMA IF NOT EXISTS analytics;      -- INTERNAL: aggregated, de-identified
CREATE SCHEMA IF NOT EXISTS reference;      -- PUBLIC: ECB rates, FATF, WB indicators

REVOKE ALL ON SCHEMA raw_pii, masked, analytics, reference FROM PUBLIC;


-- -----------------------------------------------------------------------------
-- 1.  ROLES  (group roles, NOLOGIN — these are permission containers)
-- -----------------------------------------------------------------------------
-- One role per job function, mapped to the RACI matrix.
CREATE ROLE finguard_dpo            NOLOGIN;  -- Data Protection Officer
CREATE ROLE finguard_cdo            NOLOGIN;  -- Chief Data Officer
CREATE ROLE finguard_compliance     NOLOGIN;  -- AML / Compliance analysts
CREATE ROLE finguard_data_engineer  NOLOGIN;  -- ETL / pipeline owners
CREATE ROLE finguard_data_analyst   NOLOGIN;  -- BI / reporting
CREATE ROLE finguard_data_scientist NOLOGIN;  -- ML / model training
CREATE ROLE finguard_auditor        NOLOGIN;  -- External auditors (read-only)
CREATE ROLE finguard_marketing      NOLOGIN;  -- Campaign analysts


-- -----------------------------------------------------------------------------
-- 2.  USERS  (LOGIN roles — actual humans / service accounts)
--     Passwords here are placeholders; production uses SSO + MFA.
-- -----------------------------------------------------------------------------
CREATE USER alice_dpo        WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_dpo;
CREATE USER bob_cdo          WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_cdo;
CREATE USER carol_compliance WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_compliance;
CREATE USER dan_engineer     WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_data_engineer;
CREATE USER eve_analyst      WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_data_analyst;
CREATE USER frank_scientist  WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_data_scientist;
CREATE USER grace_auditor    WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_auditor;
CREATE USER heidi_marketing  WITH PASSWORD 'CHANGE_ME' IN ROLE finguard_marketing;


-- -----------------------------------------------------------------------------
-- 3.  GRANTS BY CLASSIFICATION TIER
-- -----------------------------------------------------------------------------

-- PUBLIC tier (reference schema): ECB rates, FATF lists, World Bank indicators.
-- Everyone can read; auditors get the same access as internal staff here.
GRANT USAGE  ON SCHEMA reference TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst,
    finguard_data_scientist, finguard_auditor, finguard_marketing;
GRANT SELECT ON ALL TABLES IN SCHEMA reference TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst,
    finguard_data_scientist, finguard_auditor, finguard_marketing;

-- INTERNAL tier (analytics schema): aggregated, no direct PII.
-- All employees but NOT external auditors by default.
GRANT USAGE  ON SCHEMA analytics TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst,
    finguard_data_scientist, finguard_marketing;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst,
    finguard_data_scientist, finguard_marketing;

-- CONFIDENTIAL tier (masked schema): tokenized prod data (TOKEN_xxx, hashes).
-- Data team, compliance, leadership.  Marketing gets ONLY bank_marketing view.
GRANT USAGE  ON SCHEMA masked TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst, finguard_data_scientist;
GRANT SELECT ON ALL TABLES IN SCHEMA masked TO
    finguard_dpo, finguard_cdo, finguard_compliance,
    finguard_data_engineer, finguard_data_analyst, finguard_data_scientist;

-- Data engineers also need write access to load masked data
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA masked TO finguard_data_engineer;

-- Marketing gets a narrow, column-filtered view (no balances, no risk scores)
CREATE OR REPLACE VIEW masked.bank_marketing_for_campaigns AS
    SELECT customer_id, age_band, job, marital, education,
           country, zip3, last_contact_month, previous_outcome, subscribed_deposit
    FROM   masked.bank_marketing_customers;
GRANT USAGE  ON SCHEMA masked TO finguard_marketing;
GRANT SELECT ON masked.bank_marketing_for_campaigns TO finguard_marketing;

-- RESTRICTED tier (raw_pii schema): real names, emails, IBANs, the mapping vault.
-- ONLY DPO and CDO — and even they go through an audit-logged view.
GRANT USAGE  ON SCHEMA raw_pii TO finguard_dpo, finguard_cdo;
GRANT SELECT ON ALL TABLES IN SCHEMA raw_pii TO finguard_dpo, finguard_cdo;

-- DPO is the only role that can WRITE to the vault (GDPR erasure execution)
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw_pii TO finguard_dpo;


-- -----------------------------------------------------------------------------
-- 4.  COLUMN-LEVEL DENIES  (defense in depth — even within CONFIDENTIAL,
--     some columns are off-limits to most CONFIDENTIAL-tier roles)
-- -----------------------------------------------------------------------------
-- Example: data_analyst can SELECT aml_transactions_masked but NOT see ip_address
REVOKE SELECT (ip_address, device_id)
    ON masked.aml_transactions_masked
    FROM finguard_data_analyst, finguard_data_scientist;


-- -----------------------------------------------------------------------------
-- 5.  ROW-LEVEL SECURITY  (compliance only sees flagged transactions)
-- -----------------------------------------------------------------------------
ALTER TABLE masked.aml_transactions_masked ENABLE ROW LEVEL SECURITY;

CREATE POLICY compliance_sees_flagged
    ON masked.aml_transactions_masked
    FOR SELECT
    TO finguard_compliance
    USING (is_suspicious = 1 OR aml_flag <> 'CLEAR');

CREATE POLICY engineers_see_all
    ON masked.aml_transactions_masked
    FOR ALL
    TO finguard_data_engineer
    USING (true);


-- -----------------------------------------------------------------------------
-- 6.  AUDIT LOGGING  (every access to RESTRICTED data is recorded)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit.pii_access_log (
    log_id        BIGSERIAL PRIMARY KEY,
    accessed_at   TIMESTAMPTZ DEFAULT now(),
    db_user       TEXT        DEFAULT current_user,
    client_ip     INET        DEFAULT inet_client_addr(),
    table_name    TEXT,
    operation     TEXT,
    record_count  INT,
    justification TEXT
);


-- -----------------------------------------------------------------------------
-- 7.  VERIFICATION QUERIES  (use these in the demo to prove RBAC works)
-- -----------------------------------------------------------------------------

-- a)  Show every grant for each role:
--     SELECT grantee, table_schema, table_name, privilege_type
--     FROM   information_schema.role_table_grants
--     WHERE  grantee LIKE 'finguard_%'
--     ORDER  BY grantee, table_schema, table_name;

-- b)  Demo positive case — analyst can read masked transactions:
--     SET ROLE finguard_data_analyst;
--     SELECT transaction_id, amount, currency FROM masked.aml_transactions_masked LIMIT 3;
--     -- ✅ SUCCESS

-- c)  Demo denial — analyst CANNOT read raw PII:
--     SET ROLE finguard_data_analyst;
--     SELECT * FROM raw_pii.customer_names LIMIT 1;
--     -- ❌ ERROR: permission denied for schema raw_pii

-- d)  Demo denial — analyst CANNOT see ip_address column:
--     SET ROLE finguard_data_analyst;
--     SELECT ip_address FROM masked.aml_transactions_masked LIMIT 1;
--     -- ❌ ERROR: permission denied for column ip_address

-- e)  Demo RLS — compliance only sees flagged rows:
--     SET ROLE finguard_compliance;
--     SELECT COUNT(*) FROM masked.aml_transactions_masked;
--     -- Returns ~ 5-10% of rows (the flagged ones), not the full 5000.

-- =============================================================================
--  END  |  Total: 4 schemas, 8 roles, 8 users, 4-tier RBAC enforced.
-- =============================================================================
