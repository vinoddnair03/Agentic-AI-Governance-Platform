# Agentic AI Governance Platform 🛡️

A production-grade web application for classifying, assessing, and governing autonomous AI agents using ReAct (Reasoning + Acting) pattern architecture.

---

## 🚀 Overview

The **Agentic AI Governance Platform** provides enterprise risk managers, compliance officers, and CTOs with an automated governance assessment for AI agent specifications. By evaluating agent capabilities, autonomy scope, human-in-the-loop oversight, and API integrations, the platform generates tailored compliance profiles, risk analyses, operational safeguards, and incident playbooks.

### Key Capabilities

- 🏷️ **Autonomy Tier Classification (0–4):** Classifies AI agents from Tier 0 (Assisted / Read-Only) to Tier 4 (Full Autonomy).
- ⚠️ **Automated Risk Assessment:** Extracts domain-specific operational, legal, security, and algorithmic bias risks.
- 🛡️ **Required Operational Safeguards:** Generates tier-tailored controls (approval gates, spending limits, emergency kill-switches).
- 📋 **Regulatory Compliance Mapping:** Maps agent profiles directly to **ISO 42001**, **NIST AI RMF**, and **EU AI Act** (High-Risk & Transparency mandates).
- 📄 **Incident Response Playbook Generation:** Automatically outputs a structured Markdown incident playbook with SEV-1 to SEV-3 protocols and 1-click clipboard copy.
- 🔄 **Side-by-Side Agent Comparison:** Compare two agent specifications side-by-side to evaluate governance delta.
- 💾 **Report Exporting:** Download full assessment reports in JSON or Markdown formats.

---

## 🏗️ Architecture & Tech Stack

```text
               ┌──────────────────────────────────────────────┐
               │    React 18 Single-Page Dashboard (Vite)     │
               └──────────────────────┬───────────────────────┘
                                      │ REST API /api/v1
                                      ▼
               ┌──────────────────────────────────────────────┐
               │          FastAPI REST Server Backend         │
               └──────────────────────┬───────────────────────┘
                                      │
               ┌──────────────────────┴───────────────────────┐
               │    Anthropic Claude API ReAct Engine Loop    │
               └──────────────────────┬───────────────────────┘
                                      │
    ┌─────────────────────────────────┴─────────────────────────────────┐
    │                    5 Locked Governance Tools                      │
    ├──────────────────────────┬──────────────────────┬─────────────────┤
    │ classify_autonomy_tier() │ assess_risks()       │ check_controls()│
    │ map_compliance()         │ generate_playbook()  │                 │
    └──────────────────────────┴──────────────────────┴─────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │    SQLite Database (governance.db Storage)    │
               └──────────────────────────────────────────────┘
```

- **Frontend:** React 18, Vite, Vanilla CSS (Cyber-dark glassmorphism design system), Lucide React icons.
- **Backend:** FastAPI (Python 3.11+), Uvicorn server, Pydantic data validation.
- **Database:** SQLite (`governance.db`) auto-initialized with `agent_specs`, `assessments`, and `assessment_results` tables.
- **AI Engine:** Anthropic Claude API SDK with tool-calling ReAct loop and deterministic fallback engine.

---

## 🛠️ The 5 Locked Governance Tools

1. `classify_autonomy_tier(agent_spec: dict) -> int`  
   Evaluates agent scope and returns an Autonomy Tier (0 to 4).
2. `assess_risks(agent_spec: dict) -> list`  
   Extracts operational, security, and compliance risks based on domain and integrations.
3. `check_controls(tier: int) -> list`  
   Retrieves mandatory operational controls and human-in-the-loop safeguards.
4. `map_compliance(tier: int) -> dict`  
   Maps agent profile to ISO 42001, NIST AI RMF, and EU AI Act requirements.
5. `generate_playbook(tier: int, risks: list) -> str`  
   Generates a Markdown incident response playbook with containment protocols.

---

## 🚦 Getting Started

### Prerequisites

- **Python:** 3.11 or higher
- **Node.js:** v18 or higher (bundled with `npm`)
- **Git:** 2.x

### 1. Clone & Environment Setup

```powershell
git clone https://github.com/vinodnair03/Agentic-AI-Governance-Platform.git
cd Agentic-AI-Governance-Platform
```

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### 2. Backend Setup

Install Python dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the FastAPI backend server:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

*API docs available at: `http://localhost:8000/docs`*

### 3. Frontend Setup

In a new terminal window:

```powershell
cd frontend
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser.

---

## 🧪 Running Automated Tests

Run the automated 6-step API and database test suite:

```powershell
python -c "import sys; sys.path.insert(0, '.'); sys.path.insert(0, r'scratch'); import test_suite; test_suite.run_tests()"
```

---

## 📄 License

MIT License. Designed for AI Governance & Compliance teams.
