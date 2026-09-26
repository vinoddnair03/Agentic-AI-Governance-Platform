import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import init_db, get_assessment_by_id
from .react_engine import run_react_governance_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Agentic AI Governance Platform API",
    description="Backend API for classifying, assessing, and governing autonomous AI agents",
    version="1.0.0",
    lifespan=lifespan
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentSpecRequest(BaseModel):
    name: str = Field(..., example="Financial Loan Agent")
    description: str = Field(..., example="Autonomous loan pre-approval agent")
    domain: str = Field(..., example="Fintech")
    autonomy_scope: str = Field(..., example="Approves loans under $10,000 without human review")
    integrations: str = Field(..., example="Credit Bureau API, Core Banking API")
    human_in_loop_level: str = Field(..., example="Periodic")

class CompareRequest(BaseModel):
    assessment_id_1: str
    assessment_id_2: str

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "Agentic AI Governance Platform API"}

@app.post("/api/v1/assess")
def create_assessment(spec: AgentSpecRequest):
    try:
        spec_dict = spec.model_dump()
        result = run_react_governance_engine(spec_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/assessment/{assessment_id}")
def get_assessment(assessment_id: str):
    res = get_assessment_by_id(assessment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return res

@app.post("/api/v1/compare")
def compare_assessments(req: CompareRequest):
    res1 = get_assessment_by_id(req.assessment_id_1)
    res2 = get_assessment_by_id(req.assessment_id_2)
    
    if not res1 or not res2:
        raise HTTPException(status_code=404, detail="One or both assessment IDs not found")
        
    return {
        "agent_1": res1,
        "agent_2": res2,
        "tier_difference": res2["autonomy_tier"] - res1["autonomy_tier"],
        "comparison_summary": f"{res1['agent_name']} (Tier {res1['autonomy_tier']}) vs {res2['agent_name']} (Tier {res2['autonomy_tier']})"
    }

@app.get("/api/v1/export/{assessment_id}")
def export_assessment(assessment_id: str, fmt: str = Query("json", alias="format", pattern="^(json|md)$")):
    res = get_assessment_by_id(assessment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if fmt == "json":
        return res
    else:
        # Markdown export format
        md_content = f"""# AI Governance Assessment Report

**Agent Name:** {res['agent_name']}  
**Assessment ID:** {res['assessment_id']}  
**Date:** {res['created_at']}  
**Autonomy Tier:** Tier {res['autonomy_tier']}  

---

## 1. Agent Specification
- **Domain:** {res['domain']}
- **Autonomy Scope:** {res['autonomy_scope']}
- **Integrations:** {res['integrations']}
- **Human-in-the-Loop Level:** {res['human_in_loop_level']}

## 2. Risk Assessment
{chr(10).join(['- ' + r for r in res['risks']])}

## 3. Required Operational Controls
{chr(10).join(['- ' + c for c in res['controls']])}

## 4. Compliance Framework Mapping
### ISO 42001
{chr(10).join(['- ' + item for item in res['compliance'].get('iso_42001', [])])}

### NIST AI RMF
{chr(10).join(['- ' + item for item in res['compliance'].get('nist_ai_rmf', [])])}

### EU AI Act
{chr(10).join(['- ' + item for item in res['compliance'].get('eu_ai_act', [])])}

---

{res['playbook_md']}
"""
        return {"filename": f"{res['agent_name'].lower().replace(' ', '_')}_report.md", "content": md_content}
