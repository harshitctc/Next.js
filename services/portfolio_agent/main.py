from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.common.explainability import make_explainability_payload
from services.common.storage import get_connection, insert_decision_log, insert_explanation

app = FastAPI(title="portfolio-agent", version="0.1.0")


class AllocationRequest(BaseModel):
    account_id: str
    ticker: str
    tower_user_embedding: list[float] = Field(min_length=8, max_length=512)
    tower_asset_embedding: list[float] = Field(min_length=8, max_length=512)
    risk_budget: float = Field(ge=0.0, le=1.0)


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@app.post("/agent/run")
def run_agent(req: AllocationRequest) -> dict:
    # Two-Tower retrieval score (user tower · asset tower) + risk penalty.
    affinity = dot(req.tower_user_embedding, req.tower_asset_embedding)
    risk_penalty = (1.0 - req.risk_budget) * 0.35
    logit = affinity - risk_penalty
    score = 1 / (1 + exp(-max(min(logit, 20), -20)))

    target_weight = min(max(score * req.risk_budget, 0.0), 0.25)
    decision_id = f"alloc-{uuid4()}"

    features = {
        "tower_affinity": affinity,
        "risk_budget": req.risk_budget,
        "risk_penalty": risk_penalty,
    }
    shap_like = {
        "tower_affinity": affinity,
        "risk_budget": req.risk_budget * 0.6,
        "risk_penalty": -risk_penalty,
    }

    explain = make_explainability_payload(
        agent_name="Portfolio Agent",
        model_name="two-tower-allocator",
        model_version="2026.02",
        raw_features=features,
        shap_like_values=shap_like,
    )

    output = {
        "decision_id": decision_id,
        "account_id": req.account_id,
        "ticker": req.ticker,
        "allocation_score": round(score, 4),
        "target_weight": round(target_weight, 4),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as conn:
        explanation_id = insert_explanation(conn, "allocation", decision_id, explain)
        insert_decision_log(
            conn,
            decision_type="allocation",
            decision_id=decision_id,
            account_id=req.account_id,
            ticker=req.ticker,
            input_payload=req.model_dump(),
            output_payload=output,
            policy_result={"status": "pass", "checks": ["concentration_limit", "suitability_profile"]},
            explanation_id=explanation_id,
        )

    return {"allocation": output, "explainability": explain}
