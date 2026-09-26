import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from backend import react_engine, tools
from tests.conftest import TIER_0_SPEC, TIER_4_SPEC

FAKE_KEY = "sk-ant-test-key"


def tool_use(name, input_, id_):
    return SimpleNamespace(type="tool_use", name=name, input=input_, id=id_)


class FakeClient:
    """Replays scripted responses and records every request sent to messages.create."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if isinstance(self.responses[0], Exception):
            raise self.responses.pop(0)
        return self.responses.pop(0)


@pytest.fixture
def fake_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)

    def install(responses):
        fake = FakeClient(responses)
        monkeypatch.setattr(react_engine.anthropic, "Anthropic", lambda **_: fake)
        return fake

    return install


def all_tools_in_one_turn(spec_override=None, tier_override=None):
    return SimpleNamespace(stop_reason="tool_use", content=[
        tool_use("classify_autonomy_tier", {"agent_spec": spec_override or {}}, "t1"),
        tool_use("assess_risks", {"agent_spec": spec_override or {}}, "t2"),
        tool_use("check_controls", {"tier": tier_override}, "t3"),
        tool_use("map_compliance", {"tier": tier_override}, "t4"),
        tool_use("generate_playbook", {"tier": tier_override, "risks": []}, "t5"),
    ])


END = SimpleNamespace(stop_reason="end_turn", content=[])


def test_offline_mode_never_calls_claude(monkeypatch):
    def boom(**_):
        raise AssertionError("Claude client should not be constructed without a key")
    monkeypatch.setattr(react_engine.anthropic, "Anthropic", boom)

    result = react_engine.run_react_governance_engine(TIER_4_SPEC)
    assert result["autonomy_tier"] == 4


@pytest.mark.parametrize("key", ["", "sk-ant-your-key-here", "not-an-anthropic-key"])
def test_placeholder_keys_use_offline_mode(monkeypatch, key):
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    monkeypatch.setattr(react_engine.anthropic, "Anthropic", lambda **_: pytest.fail("should not call Claude"))
    assert react_engine.run_react_governance_engine(TIER_0_SPEC)["autonomy_tier"] == 0


def test_model_supplied_arguments_cannot_change_the_result(fake_claude):
    """Prompt injection: Claude is tricked into passing a 'read-only' spec and tier 0."""
    injected = {"autonomy_scope": "read-only", "human_in_loop_level": "Human approves all outputs"}
    fake_claude([all_tools_in_one_turn(spec_override=injected, tier_override=0), END])

    result = react_engine.run_react_governance_engine(TIER_4_SPEC)

    assert result["autonomy_tier"] == 4
    assert result["controls"] == tools.check_controls(4)
    assert result["compliance"] == tools.map_compliance(4)


def test_tier_0_is_not_promoted_to_tier_2(fake_claude):
    """Previously `tier or 2` turned a legitimate tier 0 into tier 2 defaults."""
    fake_claude([all_tools_in_one_turn(tier_override="0"), END])

    result = react_engine.run_react_governance_engine(TIER_0_SPEC)

    assert result["autonomy_tier"] == 0
    assert result["controls"] == tools.check_controls(0)


def test_tool_results_sent_to_claude_are_trusted_outputs(fake_claude):
    fake = fake_claude([all_tools_in_one_turn(), END])

    react_engine.run_react_governance_engine(TIER_4_SPEC)

    results_msg = fake.requests[1]["messages"][-1]
    assert results_msg["role"] == "user"
    by_id = {r["tool_use_id"]: json.loads(r["content"]) for r in results_msg["content"]}
    assert by_id["t1"] == 4
    assert by_id["t3"] == tools.check_controls(4)
    assert fake.requests[0]["model"] == react_engine.CLAUDE_MODEL


def test_unknown_tool_returns_error_result(fake_claude):
    fake = fake_claude([
        SimpleNamespace(stop_reason="tool_use", content=[tool_use("delete_everything", {}, "x1")]),
        END,
    ])

    react_engine.run_react_governance_engine(TIER_0_SPEC)

    result = fake.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True


def test_loop_stops_after_max_iterations(fake_claude):
    looping = SimpleNamespace(stop_reason="tool_use", content=[tool_use("assess_risks", {}, "r")])
    fake = fake_claude([looping] * (react_engine.MAX_REACT_ITERATIONS + 5))

    react_engine.run_react_governance_engine(TIER_0_SPEC)

    assert len(fake.requests) == react_engine.MAX_REACT_ITERATIONS


def test_api_failure_falls_back_and_logs(fake_claude, caplog):
    error = anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    fake_claude([error])

    result = react_engine.run_react_governance_engine(TIER_4_SPEC)

    assert result["autonomy_tier"] == 4
    assert "falling back to direct execution" in caplog.text


def test_result_is_persisted_with_created_at(fake_claude):
    fake_claude([END])

    result = react_engine.run_react_governance_engine(TIER_0_SPEC)

    assert result["assessment_id"].startswith("assess_")
    assert result["status"] == "COMPLETED"
    assert result["created_at"]
