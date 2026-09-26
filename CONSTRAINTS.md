# Project Constraints & Architectural Decisions

## Tech Stack (LOCKED)

- **Frontend:** React 18 (JavaScript, single-page app)
- **Backend:** FastAPI (Python 3.11+, REST API)
- **Database:** SQLite (file-based, auto-created)
- **AI Engine:** Anthropic Claude API via ReAct loop
- **Version Control:** Git / GitHub (`vinodnair03/Agentic-AI-Governance-Platform`)

## Core Tools (LOCKED - ReAct Loop)

The governance engine MUST implement and execute exactly these 5 tools:

1. `classify_autonomy_tier(agent_spec: dict) -> int` (Returns Tier 0-4)
2. `assess_risks(agent_spec: dict) -> list` (Returns list of risk factors)
3. `check_controls(tier: int) -> list` (Returns operational controls)
4. `map_compliance(tier: int) -> dict` (Returns ISO 42001, NIST AI RMF, EU AI Act mapping)
5. `generate_playbook(tier: int, risks: list) -> str` (Returns incident response playbook markdown)

## Scope & Execution Constraints

- Database: Simple SQLite schema (`agent_specs`, `assessments`, `results`)
- Endpoints: `/assess`, `/compare`, `/export`
- UI: Single-page form → results → export dashboard
- No scope additions or unnecessary dependencies
