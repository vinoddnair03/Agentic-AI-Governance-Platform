import inspect

import pytest

from backend import tools
from tests.conftest import TIER_0_SPEC, TIER_2_SPEC, TIER_4_SPEC


def test_locked_tool_signatures():
    expected = {
        "classify_autonomy_tier": ["agent_spec"],
        "assess_risks": ["agent_spec"],
        "check_controls": ["tier"],
        "map_compliance": ["tier"],
        "generate_playbook": ["tier", "risks"],
    }
    for name, params in expected.items():
        assert list(inspect.signature(getattr(tools, name)).parameters) == params


@pytest.mark.parametrize("spec, tier", [(TIER_0_SPEC, 0), (TIER_2_SPEC, 2), (TIER_4_SPEC, 4)])
def test_presets_classify_to_their_labelled_tier(spec, tier):
    assert tools.classify_autonomy_tier(spec) == tier


def test_periodic_review_is_tier_3():
    spec = {"autonomy_scope": "Executes disbursement without human review", "human_in_loop_level": "Periodic Review"}
    assert tools.classify_autonomy_tier(spec) == 3


def test_classify_returns_int_in_range_for_empty_spec():
    assert tools.classify_autonomy_tier({}) in range(5)


def test_assess_risks_domain_specific():
    risks = tools.assess_risks(TIER_2_SPEC)
    assert any("Financial" in r for r in risks)
    assert all(isinstance(r, str) for r in risks)


def test_assess_risks_never_empty():
    assert tools.assess_risks({"domain": "Other", "autonomy_scope": "", "integrations": ""})


@pytest.mark.parametrize("tier", range(5))
def test_check_controls_includes_base_controls(tier):
    controls = tools.check_controls(tier)
    assert controls[0].startswith("Audit logging")
    assert len(controls) > 2


def test_tier_0_controls_require_human_confirmation():
    assert any("Human confirmation" in c for c in tools.check_controls(0))


@pytest.mark.parametrize("tier, high_risk", [(0, False), (1, False), (2, True), (4, True)])
def test_map_compliance_eu_ai_act_risk_class(tier, high_risk):
    mapping = tools.map_compliance(tier)
    assert set(mapping) == {"iso_42001", "nist_ai_rmf", "eu_ai_act"}
    assert ("High-Risk" in mapping["eu_ai_act"][0]) is high_risk


def test_generate_playbook_lists_risks_and_tier():
    md = tools.generate_playbook(3, ["Risk A", "Risk B"])
    assert md.startswith("# Incident Response Playbook (Tier 3 Autonomy)")
    assert "- **Risk A**" in md and "- **Risk B**" in md
