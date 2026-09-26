import pytest

from backend import main
from tests.conftest import TIER_0_SPEC, TIER_2_SPEC, TIER_4_SPEC

API = "/api/v1"


def assess(client, spec):
    res = client.post(f"{API}/assess", json=spec)
    assert res.status_code == 200, res.text
    return res.json()


def test_health(client):
    res = client.get(f"{API}/health")
    assert res.json() == {"status": "ok", "service": "Agentic AI Governance Platform API"}


def test_assess_returns_full_assessment(client):
    body = assess(client, TIER_2_SPEC)
    assert body["autonomy_tier"] == 2
    assert body["autonomy_tier_label"] == "Tier 2: Conditional Autonomy"
    assert body["agent_name"] == TIER_2_SPEC["name"]
    for key in ("risks", "controls", "compliance", "playbook_md", "created_at", "status"):
        assert body[key]


def test_post_and_get_return_the_same_assessment(client):
    created = assess(client, TIER_0_SPEC)
    fetched = client.get(f"{API}/assessment/{created['assessment_id']}").json()
    assert fetched == created


def test_get_unknown_assessment_is_404(client):
    assert client.get(f"{API}/assessment/assess_missing").status_code == 404


def test_compare(client):
    a = assess(client, TIER_0_SPEC)
    b = assess(client, TIER_4_SPEC)
    res = client.post(f"{API}/compare", json={
        "assessment_id_1": a["assessment_id"],
        "assessment_id_2": f"  {b['assessment_id']}  ",  # pasted IDs with whitespace still work
    })
    assert res.status_code == 200
    body = res.json()
    assert body["tier_difference"] == 4
    assert body["comparison_summary"] == f"{TIER_0_SPEC['name']} (Tier 0) vs {TIER_4_SPEC['name']} (Tier 4)"


def test_compare_unknown_id_is_404(client):
    a = assess(client, TIER_0_SPEC)
    res = client.post(f"{API}/compare", json={"assessment_id_1": a["assessment_id"], "assessment_id_2": "nope"})
    assert res.status_code == 404


def test_export_json(client):
    a = assess(client, TIER_2_SPEC)
    res = client.get(f"{API}/export/{a['assessment_id']}?format=json")
    assert res.json() == a


def test_export_markdown(client):
    a = assess(client, TIER_4_SPEC)
    body = client.get(f"{API}/export/{a['assessment_id']}?format=md").json()
    assert body["filename"] == "hft_liquidity_arbitrage_agent_report.md"
    assert body["content"].startswith("# AI Governance Assessment Report")
    assert "**Autonomy Tier:** Tier 4" in body["content"]
    assert "# Incident Response Playbook" in body["content"]


def test_export_filename_cannot_escape_directory(client):
    a = assess(client, {**TIER_0_SPEC, "name": "../../Windows/evil name"})
    filename = client.get(f"{API}/export/{a['assessment_id']}?format=md").json()["filename"]
    assert "/" not in filename and "\\" not in filename and ".." not in filename


def test_export_rejects_unknown_format(client):
    a = assess(client, TIER_0_SPEC)
    assert client.get(f"{API}/export/{a['assessment_id']}?format=xml").status_code == 422


def test_export_unknown_assessment_is_404(client):
    assert client.get(f"{API}/export/assess_missing").status_code == 404


@pytest.mark.parametrize("field, value", [
    ("name", ""),
    ("name", "   "),
    ("name", "x" * (main.SHORT_TEXT + 1)),
    ("description", "x" * (main.LONG_TEXT + 1)),
])
def test_assess_rejects_invalid_input(client, field, value):
    res = client.post(f"{API}/assess", json={**TIER_0_SPEC, field: value})
    assert res.status_code == 422


def test_assess_rejects_missing_field(client):
    spec = {k: v for k, v in TIER_0_SPEC.items() if k != "integrations"}
    assert client.post(f"{API}/assess", json=spec).status_code == 422


def test_internal_errors_do_not_leak_details(client, monkeypatch):
    def fail(_spec):
        raise RuntimeError("secret internal path C:\\db\\governance.db")
    monkeypatch.setattr(main, "run_react_governance_engine", fail)

    res = client.post(f"{API}/assess", json=TIER_0_SPEC)
    assert res.status_code == 500
    assert "secret" not in res.text


def test_cors_allows_configured_origin(client):
    res = client.options(f"{API}/assess", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    })
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
