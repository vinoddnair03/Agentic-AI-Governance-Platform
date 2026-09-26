import os
import json
import uuid
import logging
import anthropic
from typing import Dict, Any
from dotenv import load_dotenv

from .tools import (
    classify_autonomy_tier,
    assess_risks,
    check_controls,
    map_compliance,
    generate_playbook
)
from .database import save_assessment, TIER_LABELS

logger = logging.getLogger(__name__)

load_dotenv()

TOOL_SCHEMAS = [
    {
        "name": "classify_autonomy_tier",
        "description": "Classifies agent spec into Autonomy Tier 0 (No Autonomy) to Tier 4 (Full Autonomy)",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_spec": {"type": "object", "description": "Agent specification dictionary"}
            },
            "required": ["agent_spec"]
        }
    },
    {
        "name": "assess_risks",
        "description": "Analyzes agent spec for operational, legal, technical, and security risks",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_spec": {"type": "object", "description": "Agent specification dictionary"}
            },
            "required": ["agent_spec"]
        }
    },
    {
        "name": "check_controls",
        "description": "Retrieves required operational safeguards tailored to autonomy tier",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "integer", "description": "Autonomy tier (0-4)"}
            },
            "required": ["tier"]
        }
    },
    {
        "name": "map_compliance",
        "description": "Maps tier and domain to ISO 42001, NIST AI RMF, and EU AI Act requirements",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "integer", "description": "Autonomy tier (0-4)"}
            },
            "required": ["tier"]
        }
    },
    {
        "name": "generate_playbook",
        "description": "Generates markdown incident response playbook based on tier and risks",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "integer", "description": "Autonomy tier (0-4)"},
                "risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of identified risks"
                }
            },
            "required": ["tier", "risks"]
        }
    }
]


def run_fallback_assessment(agent_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the 5 tools directly when API key is unavailable or during fast offline execution.
    """
    tier = classify_autonomy_tier(agent_spec)
    risks = assess_risks(agent_spec)
    controls = check_controls(tier)
    compliance = map_compliance(tier)
    playbook = generate_playbook(tier, risks)

    spec_id = f"spec_{uuid.uuid4().hex[:8]}"
    assessment_id = f"assess_{uuid.uuid4().hex[:8]}"

    save_assessment(
        assessment_id=assessment_id,
        spec_id=spec_id,
        spec_data=agent_spec,
        tier=tier,
        risks=risks,
        controls=controls,
        compliance=compliance,
        playbook_md=playbook
    )

    return {
        "assessment_id": assessment_id,
        "agent_name": agent_spec.get("name", "Unnamed Agent"),
        "description": agent_spec.get("description", ""),
        "domain": agent_spec.get("domain", ""),
        "autonomy_scope": agent_spec.get("autonomy_scope", ""),
        "integrations": agent_spec.get("integrations", ""),
        "human_in_loop_level": agent_spec.get("human_in_loop_level", ""),
        "autonomy_tier": tier,
        "autonomy_tier_label": TIER_LABELS.get(tier, f"Tier {tier}"),
        "risks": risks,
        "controls": controls,
        "compliance": compliance,
        "playbook_md": playbook
    }


def run_react_governance_engine(agent_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the ReAct loop with Anthropic Claude API using function calls.
    Falls back to direct tool execution if ANTHROPIC_API_KEY is not set or invalid.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or "your-key-here" in api_key or not api_key.startswith("sk-ant"):
        return run_fallback_assessment(agent_spec)

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0)
        
        system_prompt = (
            "You are an expert AI Governance Officer conducting a compliance assessment. "
            "You MUST call all 5 governance tools in sequence to evaluate the agent spec:\n"
            "1. classify_autonomy_tier\n"
            "2. assess_risks\n"
            "3. check_controls\n"
            "4. map_compliance\n"
            "5. generate_playbook\n"
            "Gather all tool outputs and complete the governance assessment."
        )

        messages = [
            {
                "role": "user",
                "content": f"Please conduct a governance assessment for this agent specification:\n{json.dumps(agent_spec, indent=2)}"
            }
        ]

        # ReAct execution loop (max 10 iterations)
        tier = None
        risks = []
        controls = []
        compliance = {}
        playbook = ""

        for _ in range(10):
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                tools=TOOL_SCHEMAS,
                messages=messages
            )

            # Check if tools were called
            tool_calls = [block for block in response.content if block.type == "tool_use"]
            if not tool_calls:
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in tool_calls:
                t_name = tool_use.name
                t_args = tool_use.input

                if t_name == "classify_autonomy_tier":
                    res = classify_autonomy_tier(t_args.get("agent_spec", agent_spec))
                    tier = res
                elif t_name == "assess_risks":
                    res = assess_risks(t_args.get("agent_spec", agent_spec))
                    risks = res
                elif t_name == "check_controls":
                    res = check_controls(t_args.get("tier", tier or 2))
                    controls = res
                elif t_name == "map_compliance":
                    res = map_compliance(t_args.get("tier", tier or 2))
                    compliance = res
                elif t_name == "generate_playbook":
                    res = generate_playbook(t_args.get("tier", tier or 2), t_args.get("risks", risks))
                    playbook = res
                else:
                    res = "Tool not found"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(res)
                })

            messages.append({"role": "user", "content": tool_results})

        # Ensure defaults if any tool was skipped
        if tier is None:
            tier = classify_autonomy_tier(agent_spec)
        if not risks:
            risks = assess_risks(agent_spec)
        if not controls:
            controls = check_controls(tier)
        if not compliance:
            compliance = map_compliance(tier)
        if not playbook:
            playbook = generate_playbook(tier, risks)

        spec_id = f"spec_{uuid.uuid4().hex[:8]}"
        assessment_id = f"assess_{uuid.uuid4().hex[:8]}"

        save_assessment(
            assessment_id=assessment_id,
            spec_id=spec_id,
            spec_data=agent_spec,
            tier=tier,
            risks=risks,
            controls=controls,
            compliance=compliance,
            playbook_md=playbook
        )

        return {
            "assessment_id": assessment_id,
            "agent_name": agent_spec.get("name", "Unnamed Agent"),
            "description": agent_spec.get("description", ""),
            "domain": agent_spec.get("domain", ""),
            "autonomy_scope": agent_spec.get("autonomy_scope", ""),
            "integrations": agent_spec.get("integrations", ""),
            "human_in_loop_level": agent_spec.get("human_in_loop_level", ""),
            "autonomy_tier": tier,
            "autonomy_tier_label": TIER_LABELS.get(tier, f"Tier {tier}"),
            "risks": risks,
            "controls": controls,
            "compliance": compliance,
            "playbook_md": playbook
        }

    except Exception as e:
        logger.warning("Claude API call failed, falling back to direct execution: %s", e)
        return run_fallback_assessment(agent_spec)
