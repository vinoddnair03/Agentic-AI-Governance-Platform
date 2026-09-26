# Authoritative Operational & Onboarding Runbook 🛡️

**Project:** Agentic AI Governance Platform  
**Target Audience:** New Developers, Maintainers, QA Engineers, and Technical Operations  
**Last Updated:** September 2026  

---

## 📋 Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Environment Configuration (`.env`)](#3-environment-configuration-env)
4. [Backend Setup & Launch](#4-backend-setup--launch)
5. [Frontend Setup & Launch](#5-frontend-setup--launch)
6. [End-to-End Functional Verification](#6-end-to-end-functional-verification)
7. [API Smoke Test](#7-api-smoke-test)
8. [Architecture Map & Key Source Code Links](#8-architecture-map--key-source-code-links)
9. [Troubleshooting & Common Issues](#9-troubleshooting--common-issues)
10. [Architecture Constraints & Code Lock Policy](#10-architecture-constraints--code-lock-policy)

---

## 1. Overview & Architecture

The **Agentic AI Governance Platform** is a full-stack web application designed to classify autonomous AI agents into Autonomy Tiers (0–4) and generate regulatory risk assessments, operational safeguards, compliance framework mappings (ISO 42001, NIST AI RMF, EU AI Act), and incident response playbooks.

### System Flow
```text
[ React 18 Frontend (Vite) @ :3000 ]
              │
              ▼ REST API (/api/v1)
[ FastAPI Backend (Uvicorn) @ :8000 ]
              │
              ▼
   [ ReAct Engine (Claude API / Fallback) ]
              │
              ├──▶ 1. classify_autonomy_tier()
              ├──▶ 2. assess_risks()
              ├──▶ 3. check_controls()
              ├──▶ 4. map_compliance()
              └──▶ 5. generate_playbook()
              │
              ▼
    [ SQLite DB (governance.db) ]
```

### Autonomy Tiers
The tier drives which controls, compliance mappings, and playbook content are generated. Higher tier = less human oversight = stricter requirements.

| Tier | Label | Meaning |
|---|---|---|
| 0 | Assisted / Read-Only | Answers or recommends; takes no autonomous actions. |
| 1 | Partial Autonomy | Performs narrow actions; humans approve most outcomes. |
| 2 | Conditional Autonomy | Acts on its own within thresholds; exceptions go to a human. |
| 3 | High Autonomy | Acts independently with only periodic human review. |
| 4 | Full Autonomy | Self-directed execution with no human in the loop. |

Labels come from `TIER_LABELS` in [backend/database.py](backend/database.py); classification logic lives in `classify_autonomy_tier()` in [backend/tools.py](backend/tools.py).

---

## 2. Prerequisites & System Requirements

Ensure the following tools are installed on your workstation:

* **Python:** 3.11+ ([Download Python](https://www.python.org/))
* **Node.js:** v18.0.0+ with `npm` v9+ ([Download Node.js](https://nodejs.org/))
* **Git:** 2.x+
* **OS Compatibility:** Windows 10/11 (PowerShell or CMD), macOS, Linux.

---

## 3. Environment Configuration (`.env`)

Create or update the `.env` file in the **project root** (not inside `backend/`):

```env
# Path: .env
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> [!NOTE]
> **Offline / Fallback Mode:**  
> The backend runs the 5 governance tools directly (no Claude call) in either of these cases:
> * **Key missing or malformed** — `ANTHROPIC_API_KEY` is unset, still contains the `your-key-here` placeholder, or doesn't start with `sk-ant`. Fallback happens immediately.
> * **Claude API call fails** — e.g. a revoked key (401), rate limit (429), network error, or a retired model. The error is logged as a **warning in the backend terminal** and the request silently falls back; the UI still shows a successful result.
>
> Fallback output is deterministic, so the full UI and API can be demonstrated without an Anthropic subscription. **If you expect live Claude results, watch the backend log** for `Claude API call failed, falling back to direct execution`.

> [!IMPORTANT]
> The Claude model is hardcoded in [backend/react_engine.py](backend/react_engine.py) as `claude-3-5-sonnet-20241022`. If that model is retired, every live call will fall back to offline mode (see above).

---

## 4. Backend Setup & Launch

All backend commands must be run from the **project root** (the folder containing `backend/` and `frontend/`), because Uvicorn imports the app as `backend.main`.

### Step 1: Create & Activate a Virtual Environment (recommended)
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r backend/requirements.txt
```

### Step 3: Start the FastAPI Server
From the project root, launch the backend on port `8000`:

```bash
uvicorn backend.main:app --reload --port 8000
```

> Running this from inside `backend/` fails with `ModuleNotFoundError: No module named 'backend'`.

The SQLite database `backend/governance.db` is created automatically on first startup.

### Step 4: Verify Backend Health
* **Health Check API:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) (Expected output: `{"status": "ok", "service": "Agentic AI Governance Platform API"}`)
* **Interactive OpenAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. Frontend Setup & Launch

Open a **second terminal window** (leave the backend running) and navigate to the `frontend` directory.

### Step 1: Install Node Dependencies
```bash
cd frontend
npm install
```

### Step 2: Start the Vite Dev Server
```bash
npm run dev
```

### Step 3: Open Dashboard
Access the frontend UI at: **[http://localhost:3000](http://localhost:3000)**

*The Vite dev server automatically proxies `/api/*` requests to the FastAPI backend running at `http://localhost:8000`.*

---

## 6. End-to-End Functional Verification

Follow this standard verification script to confirm system operation:

1. **Submit Agent Specification:**
   * Open [http://localhost:3000](http://localhost:3000).
   * **Fastest path:** under **Quick Load Case Studies**, click a preset (`Tier 0: FAQ Support Bot`, `Tier 2: Loan Approval Agent`, or `Tier 4: Autonomous Trader`) to fill the form automatically.
   * **Or fill the form manually:**
     * **Agent Name:** `Autonomous Finance Agent`
     * **Domain / Industry:** `Fintech`
     * **Description:** `Pre-approves small business loans up to $25,000`
     * **Autonomy Scope & Action Boundaries:** `Executes credit evaluation & disbursement without human review`
     * **Integrations & External APIs:** `Credit Bureau API, Core Banking API`
     * **Human-in-the-Loop Level:** `Periodic Review`
   * Click **Run Governance Assessment**.
2. **Review Generated Governance Output:**
   * Verify the **Autonomy Tier Badge** (the manual example above should land at Tier 3 or Tier 4 — see [Autonomy Tiers](#autonomy-tiers)).
   * **Note the Assessment ID** shown under the agent name (`ID: assess_xxxxxxxx`). You'll need it for comparison.
   * Confirm **Identified Risks** and **Required Controls** are populated.
   * Verify **Compliance Mapping** across ISO 42001, NIST AI RMF, and EU AI Act.
   * Review the generated **Incident Response Playbook**; the **Copy Markdown** button copies it to the clipboard.
3. **Test Assessment Comparison:**
   * Run a second assessment with a different tier (e.g. the `Tier 0: FAQ Support Bot` preset) and note its Assessment ID.
   * Switch to the **Compare Agents** tab.
   * Paste the two IDs into **First Assessment ID** and **Second Assessment ID**, then click **Compare Agents**.
   * Verify both tier badges and the tier difference are shown.
4. **Test Report Export:**
   * **JSON:** click **Export Assessment JSON** below the results to download the full assessment.
   * **Markdown:** there's no UI button for the full Markdown report; use the API instead (see [§7](#7-api-smoke-test)). The response is JSON of the form `{"filename": "...", "content": "<markdown>"}`.

---

## 7. API Smoke Test

There is no automated test suite yet. The script below exercises every endpoint manually. Run it in PowerShell from any directory while the backend is running.

```powershell
$base = "http://localhost:8000/api/v1"

# 1. Health check
Invoke-RestMethod -Uri "$base/health"

# 2. Create two assessments
$spec1 = @{
    name = "Test Agent"
    description = "E2E Test Agent"
    domain = "Healthcare"
    autonomy_scope = "Diagnostic assistance"
    integrations = "EMR Database"
    human_in_loop_level = "Human approves all outputs"
} | ConvertTo-Json

$spec2 = @{
    name = "Autonomous Trader"
    description = "Self-executing trading engine"
    domain = "Financial Markets"
    autonomy_scope = "Fully autonomous order routing without human intervention"
    integrations = "Exchange APIs"
    human_in_loop_level = "None (Full Autonomy)"
} | ConvertTo-Json

$a1 = Invoke-RestMethod -Uri "$base/assess" -Method Post -ContentType "application/json" -Body $spec1
$a2 = Invoke-RestMethod -Uri "$base/assess" -Method Post -ContentType "application/json" -Body $spec2
Write-Host "Created $($a1.assessment_id) (Tier $($a1.autonomy_tier)) and $($a2.assessment_id) (Tier $($a2.autonomy_tier))"

# 3. Retrieve an assessment
$retrieved = Invoke-RestMethod -Uri "$base/assessment/$($a1.assessment_id)"
Write-Host "Fetched assessment for: $($retrieved.agent_name)"

# 4. Compare the two
$cmp = @{ assessment_id_1 = $a1.assessment_id; assessment_id_2 = $a2.assessment_id } | ConvertTo-Json
$diff = Invoke-RestMethod -Uri "$base/compare" -Method Post -ContentType "application/json" -Body $cmp
Write-Host "Compare: $($diff.comparison_summary) | tier difference = $($diff.tier_difference)"

# 5. Export as JSON and Markdown
Invoke-RestMethod -Uri "$base/export/$($a1.assessment_id)?format=json" | Out-Null
$md = Invoke-RestMethod -Uri "$base/export/$($a1.assessment_id)?format=md"
$md.content | Out-File -Encoding utf8 $md.filename
Write-Host "Markdown report saved to $($md.filename)"
```

macOS / Linux users can call the same endpoints with `curl`, or use the **Try it out** buttons in the Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 8. Architecture Map & Key Source Code Links

* 📄 **Operational Rules & Constraints:** [CONSTRAINTS.md](CONSTRAINTS.md)
* 📄 **Claude Guidance File:** [CLAUDE.md](CLAUDE.md)
* ⚙️ **FastAPI Main Endpoints:** [backend/main.py](backend/main.py)
* 🧠 **ReAct AI Agent Loop:** [backend/react_engine.py](backend/react_engine.py)
* 🛠️ **Governance Tools Engine:** [backend/tools.py](backend/tools.py)
* 💾 **SQLite Persistence Layer:** [backend/database.py](backend/database.py)
* 🎨 **Frontend App UI Component:** [frontend/src/App.jsx](frontend/src/App.jsx)
* 🎨 **CSS Token System:** [frontend/src/index.css](frontend/src/index.css)

---

## 9. Troubleshooting & Common Issues

| Issue / Symptom | Root Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Uvicorn was started from inside `backend/`. | `cd` to the project root and rerun `uvicorn backend.main:app --reload --port 8000`. |
| `Port 8000 already in use` | Another Uvicorn or Python process is running on port 8000. | Kill process on 8000 (`Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess \| Stop-Process` on Windows) or run on `--port 8001` (then update the proxy target in `frontend/vite.config.js`). |
| `Port 3000 already in use` | Another Vite process is running. | Vite will auto-switch to 3001; add that origin to `ALLOWED_ORIGINS` or stop the existing Vite server. |
| `CORS Error in Browser` | Frontend origin not listed in `ALLOWED_ORIGINS`. | Update `ALLOWED_ORIGINS` in `.env` to include your frontend URL and restart the backend. |
| Assessment/compare returns "Assessment not found" | Wrong ID, or the database was reset. | Copy the ID exactly as shown in the results header (`assess_xxxxxxxx`). |
| `SQLite OperationalError` | `governance.db` locked or corrupted. | Delete `backend/governance.db` and restart the backend server; `init_db()` will recreate fresh tables automatically. **This deletes all saved assessments.** |
| Results look identical every run / no Claude reasoning | Backend is in offline fallback mode (bad key, 401/429, network error, or retired model). The UI does **not** show this error. | Check the backend terminal for `Claude API call failed, falling back to direct execution: ...` and fix the cause shown (key, quota, or model name). |

---

## 10. Architecture Constraints & Code Lock Policy

Per [CONSTRAINTS.md](CONSTRAINTS.md), the following architectural elements are **locked** and must not be altered without explicit approval:

1. **The 5 Governance Tool Signatures** in [backend/tools.py](backend/tools.py):
   * `classify_autonomy_tier(agent_spec)`
   * `assess_risks(agent_spec)`
   * `check_controls(tier)`
   * `map_compliance(tier)`
   * `generate_playbook(tier, risks)`
2. **Database Schema** in [backend/database.py](backend/database.py) (`agent_specs`, `assessments`, `assessment_results`).
3. **Core REST API Contract** in [backend/main.py](backend/main.py).
