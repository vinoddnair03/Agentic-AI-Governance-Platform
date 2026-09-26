import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app

TIER_0_SPEC = {
    "name": "Customer Support FAQ Bot",
    "description": "Read-only assistance bot answering general customer inquiries.",
    "domain": "Customer Service",
    "autonomy_scope": "Read-only Q&A. No autonomous actions or database mutations permitted.",
    "integrations": "Knowledge Base Read-Only API",
    "human_in_loop_level": "Human approves all outputs",
}

TIER_2_SPEC = {
    "name": "Financial Loan Approval Agent",
    "description": "Evaluates credit risk and approves low-risk micro-loans.",
    "domain": "Fintech / Banking",
    "autonomy_scope": "Approves loans under $10,000 without human review. Flagged loans routed to human underwriter.",
    "integrations": "Credit Bureau API, Core Banking API, Fraud Detection Engine",
    "human_in_loop_level": "Approval-Gate for transactions over threshold",
}

TIER_4_SPEC = {
    "name": "HFT Liquidity Arbitrage Agent",
    "description": "Self-executing multi-exchange cryptocurrency trading engine.",
    "domain": "Financial Markets",
    "autonomy_scope": "Fully autonomous order routing, position sizing, and goal re-balancing without human intervention.",
    "integrations": "Binance API, Coinbase Pro API, Direct Order Routing FIX Protocol",
    "human_in_loop_level": "None (Full Autonomy)",
}


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Every test gets a fresh SQLite file and runs offline unless it opts in to Claude."""
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    database.init_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
