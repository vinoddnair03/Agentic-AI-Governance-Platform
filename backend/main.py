import os
import re
import time
import uuid
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .database import init_db, get_assessment_by_id
from .react_engine import run_react_governance_engine
from .logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized successfully.")
    yield

app = FastAPI(
    title="Agentic AI Governance Platform API",
    description="Backend API for classifying, assessing, and governing autonomous AI agents",
    version="1.0.0",
    lifespan=lifespan
)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request & Error Logging Middleware
@app.middleware("http")
async def log_requests_and_errors(request: Request, call_next):
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    request.state.request_id = request_id
    start_time = time.time()

    logger.info("[%s] %s %s - Client: %s", request_id, request.method, request.url.path, request.client.host if request.client else "unknown")

    try:
        response: Response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("[%s] Completed %s %s with Status %s (%sms)", request_id, request.method, request.url.path, response.status_code, process_time_ms)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        tb = traceback.format_exc()
        logger.error("[%s] UNHANDLED ERROR on %s %s (%sms):\n%s", request_id, request.method, request.url.path, process_time_ms, tb)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "request_id": request_id,
                "message": "An unexpected server error occurred. Full details recorded in logs/error.log."
            },
            headers={"X-Request-ID": request_id}
        )

SHORT_TEXT = 200
LONG_TEXT = 4000

class AgentSpecRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=SHORT_TEXT, examples=["Financial Loan Agent"])
    description: str = Field(..., min_length=1, max_length=LONG_TEXT, examples=["Autonomous loan pre-approval agent"])
    domain: str = Field(..., min_length=1, max_length=SHORT_TEXT, examples=["Fintech"])
    autonomy_scope: str = Field(..., min_length=1, max_length=LONG_TEXT, examples=["Approves loans under $10,000 without human review"])
    integrations: str = Field(..., min_length=1, max_length=LONG_TEXT, examples=["Credit Bureau API, Core Banking API"])
    human_in_loop_level: str = Field(..., min_length=1, max_length=SHORT_TEXT, examples=["Periodic Review"])

class CompareRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    assessment_id_1: str = Field(..., max_length=64)
    assessment_id_2: str = Field(..., max_length=64)

def _safe_filename(name: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "_", name.lower()).strip("_")
    return slug or "assessment"

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "Agentic AI Governance Platform API"}

@app.post("/api/v1/assess")
def create_assessment(spec: AgentSpecRequest):
    try:
        return run_react_governance_engine(spec.model_dump())
    except Exception as exc:
        logger.error("Failed to process assessment request: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Assessment failed due to an internal server error.")

@app.get("/api/v1/assessment/{assessment_id}")
def get_assessment(assessment_id: str):
    res = get_assessment_by_id(assessment_id)
    if not res:
        logger.warning("Fetch failed: Assessment ID '%s' not found.", assessment_id)
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return res

@app.post("/api/v1/compare")
def compare_assessments(req: CompareRequest):
    res1 = get_assessment_by_id(req.assessment_id_1)
    res2 = get_assessment_by_id(req.assessment_id_2)
    
    if not res1 or not res2:
        logger.warning("Comparison failed: One or both IDs not found ('%s', '%s').", req.assessment_id_1, req.assessment_id_2)
        raise HTTPException(status_code=404, detail="One or both assessment IDs not found.")
        
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
        logger.warning("Export failed: Assessment ID '%s' not found.", assessment_id)
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")

    if fmt == "json":
        return res
    else:
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
        return {"filename": f"{_safe_filename(res['agent_name'])}_report.md", "content": md_content}
