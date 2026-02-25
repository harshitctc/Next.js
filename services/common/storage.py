from __future__ import annotations

import json
import os
from typing import Any

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agentic_finance")


def insert_explanation(conn: psycopg.Connection, decision_type: str, decision_id: str, payload: dict[str, Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO explanations (decision_type, decision_id, model_name, model_version, feature_attributions, shap_summary, explanation_text)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
            RETURNING id
            """,
            (
                decision_type,
                decision_id,
                payload["model_name"],
                payload["model_version"],
                json.dumps(payload["feature_attributions"]),
                json.dumps(payload["shap_summary"]),
                payload["explanation_text"],
            ),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0]


def insert_decision_log(
    conn: psycopg.Connection,
    decision_type: str,
    decision_id: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    policy_result: dict[str, Any],
    explanation_id: int,
    account_id: str | None = None,
    ticker: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO decision_logs (decision_type, decision_id, account_id, ticker, input_payload, output_payload, explanation_id, policy_result)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb)
            """,
            (
                decision_type,
                decision_id,
                account_id,
                ticker,
                json.dumps(input_payload),
                json.dumps(output_payload),
                explanation_id,
                json.dumps(policy_result),
            ),
        )
    conn.commit()


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)
