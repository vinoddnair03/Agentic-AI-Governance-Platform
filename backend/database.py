import sqlite3
import json
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "governance.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_specs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            domain TEXT NOT NULL,
            autonomy_scope TEXT NOT NULL,
            integrations TEXT NOT NULL,
            human_in_loop_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            agent_spec_id TEXT NOT NULL,
            autonomy_tier INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_spec_id) REFERENCES agent_specs(id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_results (
            id TEXT PRIMARY KEY,
            assessment_id TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            controls_json TEXT NOT NULL,
            compliance_json TEXT NOT NULL,
            playbook_md TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        );
        """)
        conn.commit()
    finally:
        conn.close()

def save_assessment(
    assessment_id: str,
    spec_id: str,
    spec_data: Dict[str, Any],
    tier: int,
    risks: list,
    controls: list,
    compliance: dict,
    playbook_md: str
):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO agent_specs
            (id, name, description, domain, autonomy_scope, integrations, human_in_loop_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec_id,
                spec_data.get("name", ""),
                spec_data.get("description", ""),
                spec_data.get("domain", ""),
                spec_data.get("autonomy_scope", ""),
                spec_data.get("integrations", ""),
                spec_data.get("human_in_loop_level", "")
            )
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO assessments (id, agent_spec_id, autonomy_tier, status)
            VALUES (?, ?, ?, ?)
            """,
            (assessment_id, spec_id, tier, "COMPLETED")
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO assessment_results
            (id, assessment_id, risks_json, controls_json, compliance_json, playbook_md)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"res_{assessment_id}",
                assessment_id,
                json.dumps(risks),
                json.dumps(controls),
                json.dumps(compliance),
                playbook_md
            )
        )
        conn.commit()
    finally:
        conn.close()

TIER_LABELS = {
    0: "Tier 0: Assisted / Read-Only",
    1: "Tier 1: Partial Autonomy",
    2: "Tier 2: Conditional Autonomy",
    3: "Tier 3: High Autonomy",
    4: "Tier 4: Full Autonomy"
}

def get_assessment_by_id(assessment_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
        SELECT
            a.id as assessment_id,
            a.autonomy_tier,
            a.status,
            a.created_at,
            s.name as agent_name,
            s.description,
            s.domain,
            s.autonomy_scope,
            s.integrations,
            s.human_in_loop_level,
            r.risks_json,
            r.controls_json,
            r.compliance_json,
            r.playbook_md
        FROM assessments a
        JOIN agent_specs s ON a.agent_spec_id = s.id
        JOIN assessment_results r ON r.assessment_id = a.id
        WHERE a.id = ?
        """
        cursor.execute(query, (assessment_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    tier = row["autonomy_tier"]
    return {
        "assessment_id": row["assessment_id"],
        "agent_name": row["agent_name"],
        "description": row["description"],
        "domain": row["domain"],
        "autonomy_scope": row["autonomy_scope"],
        "integrations": row["integrations"],
        "human_in_loop_level": row["human_in_loop_level"],
        "autonomy_tier": tier,
        "autonomy_tier_label": TIER_LABELS.get(tier, f"Tier {tier}"),
        "status": row["status"],
        "risks": json.loads(row["risks_json"]),
        "controls": json.loads(row["controls_json"]),
        "compliance": json.loads(row["compliance_json"]),
        "playbook_md": row["playbook_md"],
        "created_at": row["created_at"]
    }
