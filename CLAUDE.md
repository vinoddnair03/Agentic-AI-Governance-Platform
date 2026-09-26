# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic AI Governance Platform — classifies autonomous AI agents into autonomy tiers (0–4) and generates compliance assessments (risks, controls, regulatory mappings, incident playbooks) via a ReAct agent loop using the Anthropic Claude API.

## Development Commands

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # dev server on http://localhost:3000
npm run build      # production bundle → frontend/dist/
```

Both must run simultaneously. The Vite dev server proxies `/api/*` to `http://localhost:8000`.

### Environment
Copy `.env` and set your key:
```
ANTHROPIC_API_KEY=sk-ant-...
```
If the key is missing or a placeholder, the backend falls back to direct (non-Claude) tool execution — useful for offline demo.

## Architecture

```
Frontend (React 18 / Vite, port 3000)
    └── REST /api/v1  ──▶  Backend (FastAPI, port 8000)
                                └── ReAct Engine (backend/react_engine.py)
                                        └── 5 Governance Tools (backend/tools.py)
                                        └── SQLite DB (backend/governance.db)
```

### Request lifecycle
1. Frontend posts an agent spec (`POST /api/v1/assess`).
2. `react_engine.py` runs a Claude API tool-calling loop (max 10 iterations) invoking the 5 governance tools.
3. Results are persisted to SQLite via `database.py` and returned to the frontend.

### The 5 Governance Tools (`backend/tools.py`) — **locked signatures, do not alter**
| Tool | Output |
|---|---|
| `classify_autonomy_tier(agent_spec)` | `int` 0–4 |
| `assess_risks(agent_spec)` | `list[str]` |
| `check_controls(tier)` | `list[str]` |
| `map_compliance(tier)` | `dict` |
| `generate_playbook(tier, risks)` | `str` (Markdown) |

### Database (`backend/governance.db`, SQLite, auto-created)
Three tables: `agent_specs`, `assessments`, `assessment_results`. Schema is locked — do not add or modify columns.

### API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/assess` | Run assessment |
| GET | `/api/v1/assessment/{id}` | Fetch result |
| POST | `/api/v1/compare` | Compare two assessments |
| GET | `/api/v1/export/{id}?format=json\|md` | Export report |

### Claude model
Hardcoded in `react_engine.py`: `claude-3-5-sonnet-20241022`.

## Constraints (from CONSTRAINTS.md — enforced)
- **Tech stack is fixed**: React 18, FastAPI, SQLite, Anthropic SDK. No new frameworks or libraries without explicit approval.
- **Tool signatures and behavior are locked** — changes break the ReAct loop.
- **Database schema is locked** — no new columns or tables.
- **Endpoints are locked** — `/assess`, `/compare`, `/export` must remain stable.
