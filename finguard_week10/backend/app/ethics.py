"""
UNESCO Recommendation on the Ethics of AI (2021) — crosswalk for FinGuard.

The UNESCO Recommendation was adopted unanimously by all 193 member states
in November 2021. It is the first global standard-setting instrument on
AI ethics. The Recommendation defines 4 foundational values and 10
actionable principles. This module maps each principle to the FinGuard
controls that satisfy it.

Reference: https://unesdoc.unesco.org/ark:/48223/pf0000386276
"""

from __future__ import annotations
from typing import Any, Dict, List


UNESCO_VALUES: List[Dict[str, str]] = [
    {
        "id": "human_rights",
        "name": "Respect for human rights and human dignity",
        "summary": "AI must respect, protect, and promote human rights and "
                   "fundamental freedoms throughout the lifecycle.",
    },
    {
        "id": "peaceful_societies",
        "name": "Living in peaceful, just, and interconnected societies",
        "summary": "AI should foster cooperation and peaceful societies; "
                   "must not undermine social cohesion or democratic life.",
    },
    {
        "id": "diversity",
        "name": "Ensuring diversity and inclusiveness",
        "summary": "AI development must include diverse perspectives; "
                   "benefits should reach all groups, especially marginalised.",
    },
    {
        "id": "environment",
        "name": "Environment and ecosystem flourishing",
        "summary": "AI systems should support environmental sustainability.",
    },
]


UNESCO_PRINCIPLES: List[Dict[str, Any]] = [
    {
        "id": "proportionality",
        "name": "Proportionality and do-no-harm",
        "summary": "AI methods chosen must be proportionate to achieve the "
                   "stated legitimate aim, without exceeding what is necessary.",
        "finguard_controls": [
            "RBAC restricts each role to the minimum data needed",
            "Row-level security on aml_transactions limits Compliance to flagged rows only",
            "Marketing receives demographic-only narrow view (no balances or risk)",
        ],
    },
    {
        "id": "safety_security",
        "name": "Safety and security",
        "summary": "Unwanted harms (safety risks) and vulnerabilities to "
                   "attack (security risks) should be avoided and addressed.",
        "finguard_controls": [
            "AES-256-GCM authenticated encryption for the mapping vault",
            "Audit log on every read and access denial",
            "Column-level REVOKE on ip_address and device_id for analysts",
            "Two-person sign-off for GDPR erasure (DPO + CDO RACI)",
        ],
    },
    {
        "id": "fairness",
        "name": "Fairness and non-discrimination",
        "summary": "AI actors must promote social justice and safeguard "
                   "fairness; benefits should be accessible to all.",
        "finguard_controls": [
            "Week 8 disparate-impact audit on AML risk scores by FATF country list",
            "Bias monitoring on Bank Marketing campaign success by demographic",
            "Age-banding instead of exact DOB to avoid age-based targeting",
        ],
    },
    {
        "id": "sustainability",
        "name": "Sustainability",
        "summary": "Continuous assessment of AI's impact on sustainability "
                   "goals, including data minimization.",
        "finguard_controls": [
            "Data minimization — masking reduces PII footprint by ~80% at rest",
            "Retention policies enforced per classification tier",
        ],
    },
    {
        "id": "privacy",
        "name": "Right to privacy, and data protection",
        "summary": "Privacy must be respected, protected, and promoted "
                   "throughout the AI system lifecycle.",
        "finguard_controls": [
            "24 PII fields masked using 6 techniques (pseudo, hash, FPE, "
            "partial, generalize, age-band)",
            "AES-256-GCM encrypted mapping vault",
            "GDPR Art. 17 cryptographic erasure — vault entry removed, token "
            "becomes anonymous data per Recital 26",
            "DPO + CDO are the only roles that may detokenize",
        ],
    },
    {
        "id": "human_oversight",
        "name": "Human oversight and determination",
        "summary": "Member states should ensure final responsibility rests "
                   "with humans, never on AI alone.",
        "finguard_controls": [
            "DPO is Accountable for every privacy decision per RACI",
            "Two-person rule on Art. 17 erasure (CDO + DPO)",
            "AML flag is investigated by a human officer before action",
        ],
    },
    {
        "id": "transparency",
        "name": "Transparency and explainability",
        "summary": "The transparency and explainability of AI systems is "
                   "indispensable for human-rights-based, democratic societies.",
        "finguard_controls": [
            "Searchable web data catalog with column-level metadata",
            "System and column-level lineage graph",
            "Public regulation reference on every PII column",
        ],
    },
    {
        "id": "accountability",
        "name": "Responsibility and accountability",
        "summary": "Decisions on AI use must be attributable, with clear "
                   "responsibility chains.",
        "finguard_controls": [
            "RACI matrix — exactly one Accountable per governance activity",
            "Audit log records role + decision + timestamp for every access",
            "External Auditor (Deloitte) has read-only catalog access",
        ],
    },
    {
        "id": "awareness",
        "name": "Awareness and literacy",
        "summary": "Public understanding of AI and data should be promoted "
                   "through open education and engagement.",
        "finguard_controls": [
            "Data catalog is searchable by every authorised employee",
            "Each column shows its tier, owner, and the regulation governing it",
        ],
    },
    {
        "id": "governance",
        "name": "Multi-stakeholder and adaptive governance & collaboration",
        "summary": "AI governance should be inclusive, with diverse "
                   "stakeholders engaged throughout the AI lifecycle.",
        "finguard_controls": [
            "RACI includes External Auditor as a first-class role",
            "Quarterly audit log review by Compliance with sign-off by DPO",
            "Catalog enables stewards across business and tech to collaborate",
        ],
    },
]


def crosswalk() -> Dict[str, Any]:
    """Return the full UNESCO ↔ FinGuard mapping."""
    return {
        "source": "UNESCO Recommendation on the Ethics of AI (2021)",
        "url": "https://unesdoc.unesco.org/ark:/48223/pf0000386276",
        "adopted_by": "193 UNESCO member states (Nov 2021)",
        "values": UNESCO_VALUES,
        "principles": UNESCO_PRINCIPLES,
        "total_controls": sum(len(p["finguard_controls"]) for p in UNESCO_PRINCIPLES),
    }
