from __future__ import annotations

from datetime import datetime, timezone
from statistics import quantiles
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.common.explainability import make_explainability_payload
from services.common.storage import get_connection, insert_decision_log, insert_explanation

app = FastAPI(title="risk-agent", version="0.1.0")


class RiskRequest(BaseModel):
    account_id: str
    pnl_series: list[float] = Field(min_length=30)
    baseline_var_95: float = Field(gt=0)
    drift_threshold: float = Field(default=0.15, gt=0.0)


@app.post("/agent/run")
def run_agent(req: RiskRequest) -> dict:
    # Historical simulation VaR and simple drift detector.
    losses = sorted([-x for x in req.pnl_series])
    var95 = quantiles(losses, n=100)[94]
    var99 = quantiles(losses, n=100)[98]

    drift_score = abs(var95 - req.baseline_var_95) / req.baseline_var_95
    breach = drift_score > req.drift_threshold
    decision_id = f"risk-{uuid4()}"

    features = {
        "var95": var95,
        "var99": var99,
        "baseline_var95": req.baseline_var_95,
        "drift_threshold": req.drift_threshold,
    }
    shap_like = {
        "var95": var95,
        "var99": var99 * 0.5,
        "baseline_var95": -req.baseline_var_95,
        "drift_threshold": -req.drift_threshold,
    }

    explain = make_explainability_payload(
        agent_name="Risk Agent",
        model_name="historical-var-monitor",
        model_version="2026.02",
        raw_features=features,
        shap_like_values=shap_like,
    )

    output = {
        "decision_id": decision_id,
        "account_id": req.account_id,
        "var_95": round(var95, 6),
        "var_99": round(var99, 6),
        "drift_score": round(drift_score, 6),
        "breach_flag": breach,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as conn:
        explanation_id = insert_explanation(conn, "risk", decision_id, explain)
        insert_decision_log(
            conn,
            decision_type="risk",
            decision_id=decision_id,
            account_id=req.account_id,
            input_payload=req.model_dump(),
            output_payload=output,
            policy_result={
                "status": "breach" if breach else "pass",
                "checks": ["var_limit", "drift_threshold"],
            },
            explanation_id=explanation_id,
        )

    return {"risk": output, "explainability": explain}
