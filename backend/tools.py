from typing import Dict, Any, List

def classify_autonomy_tier(agent_spec: Dict[str, Any]) -> int:
    """
    Classifies an agent spec into Autonomy Tier 0 to 4.
    Tier 0: Assisted / Read-only
    Tier 1: Partial Autonomy (Routine tasks with direct human oversight)
    Tier 2: Conditional Autonomy (Independent within strict boundary, human approval gates)
    Tier 3: High Autonomy (Multi-step decisions, periodic review)
    Tier 4: Full Autonomy (Self-directing, high impact, minimal human intervention)
    """
    scope = str(agent_spec.get("autonomy_scope", "")).lower()
    hil = str(agent_spec.get("human_in_loop_level", "")).lower()
    integrations = str(agent_spec.get("integrations", "")).lower()

    if "no autonomy" in scope or "read-only" in scope or "human approves all" in hil:
        return 0
    if "full autonomy" in scope or "self-directing" in scope or "none" in hil or "no human" in hil:
        return 4
    if "high" in scope or "multi-step" in scope or "periodic" in hil:
        return 3
    if "approval" in hil or "gate" in hil or "conditional" in scope or "financial" in scope:
        return 2
    
    # Default fallback heuristics based on integrations
    if "write" in integrations or "api" in integrations:
        return 2
    return 1


def assess_risks(agent_spec: Dict[str, Any]) -> List[str]:
    """
    Returns risk factors based on agent specification details.
    """
    domain = agent_spec.get("domain", "General")
    scope = agent_spec.get("autonomy_scope", "")
    integrations = agent_spec.get("integrations", "")
    
    risks = []
    
    # Domain specific risks
    if "fin" in domain.lower() or "loan" in scope.lower() or "bank" in integrations.lower():
        risks.append("Financial loss or unauthorized monetary transactions")
        risks.append("Algorithmic credit decision bias and regulatory non-compliance")
    if "health" in domain.lower() or "patient" in scope.lower():
        risks.append("Protected Health Information (PHI) exposure and HIPAA violation")
        risks.append("Clinical decision error impacting patient care quality")
    if "customer" in domain.lower() or "chat" in scope.lower():
        risks.append("Hallucinated responses causing brand reputation damage")
        risks.append("Prompt injection attacks extracting internal knowledge base data")
        
    # Technical & integration risks
    if "api" in integrations.lower() or "db" in integrations.lower() or "database" in integrations.lower():
        risks.append("Privilege escalation via third-party API keys")
        risks.append("Unintended database mutation or data corruption")
        
    # Autonomy risks
    if not risks:
        risks.append("Unmonitored execution drift from specified operational boundaries")
        risks.append("Lack of emergency kill-switch or rollback protocol")
        
    return risks


def check_controls(tier: int) -> List[str]:
    """
    Returns required operational controls tailored to the autonomy tier.
    """
    base_controls = [
        "Audit logging of all agent prompts, tools used, and outputs",
        "Encrypted API key and secret storage (KMS / HashiCorp Vault)"
    ]
    
    tier_controls = {
        0: [
            "Human confirmation mandatory before any output is finalized"
        ],
        1: [
            "Input parameter validation and sanitization filters",
            "Rate-limiting to 60 requests per minute"
        ],
        2: [
            "Human-in-the-loop approval gate for sensitive operations",
            "Transaction monetary cap ($10,000 limit)",
            "Real-time anomaly detection for out-of-distribution inputs"
        ],
        3: [
            "Automated circuit-breaker kill switch on error threshold breach",
            "Periodic daily human supervisor audit logs review",
            "Dual-authorization protocol for agent configuration updates"
        ],
        4: [
            "Continuous automated red-teaming and adversarial testing",
            "Hardware Security Module (HSM) key management",
            "Formal verification of policy guardrails and real-time kill-switch",
            "Executive governance committee monthly oversight"
        ]
    }
    
    return base_controls + tier_controls.get(tier, tier_controls[2])


def map_compliance(tier: int) -> Dict[str, List[str]]:
    """
    Maps autonomy tier to compliance frameworks (ISO 42001, NIST AI RMF, EU AI Act).
    """
    return {
        "iso_42001": [
            "Clause 6.1.2 - AI Risk Assessment & Management",
            "Clause 8.2 - Operational Planning & Control",
            f"Clause 8.4 - Impact Assessment for Tier {tier} Deployment"
        ],
        "nist_ai_rmf": [
            "GOVERN 1.2 - Governance structures and operational policies",
            "MAP 1.1 - Context and risk characterization",
            "MEASURE 2.1 - Test, evaluation, verification, and validation (TEVV)",
            "MANAGE 1.1 - Risk treatment and mitigation strategies"
        ],
        "eu_ai_act": [
            "High-Risk AI System Classification Assessment (Annex III)" if tier >= 2 else "Limited Risk AI System (Transparency Obligations)",
            "Article 14 - Human Oversight Implementation",
            "Article 15 - Accuracy, Robustness, and Cybersecurity Requirements"
        ]
    }


def generate_playbook(tier: int, risks: List[str]) -> str:
    """
    Generates a Markdown incident response playbook.
    """
    risk_bullets = "\n".join([f"- **{r}**" for r in risks])
    
    playbook = f"""# Incident Response Playbook (Tier {tier} Autonomy)

## 1. Overview & Scope
This incident response plan applies to the Tier {tier} Autonomous Agent deployment.

## 2. Key Identified Risks
{risk_bullets}

## 3. Incident Severity Levels
- **SEV-1 (Critical):** Unauthorized high-impact action, data breach, or security bypass. Response time: < 15 minutes.
- **SEV-2 (High):** Hallucination impacting decision quality or system failure. Response time: < 1 hour.
- **SEV-3 (Medium):** Minor API failure or degraded latency. Response time: < 4 hours.

## 4. Immediate Containment Steps
1. **Kill Switch:** Trigger the emergency agent termination command or set `$env:AGENT_STATUS = "PAUSED"`.
2. **Revoke Keys:** Rotate API tokens used by the agent integration layer immediately.
3. **Isolate Database:** Pause write access for the agent service account in SQLite / DB.

## 5. Investigation & Recovery
- Inspect raw request logs in `governance.db`.
- Run forensic replay of the last 50 ReAct reasoning loops.
- Submit incident post-mortem to the AI Governance Committee.
"""
    return playbook
