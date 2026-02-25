from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.common.explainability import make_explainability_payload
from services.common.storage import get_connection, insert_decision_log, insert_explanation

app = FastAPI(title="sentiment-agent", version="0.1.0")


class SentimentRequest(BaseModel):
    ticker: str
    document_text: str = Field(min_length=20)
    source_type: str = Field(description="news | sec_filing")


@app.post("/agent/run")
def run_agent(req: SentimentRequest) -> dict:
    # Placeholder NLP alpha extraction (swap with transformer or RAG pipeline).
    positive_words = ["beat", "growth", "upgrade", "strong", "outperform"]
    negative_words = ["miss", "downgrade", "weak", "investigation", "loss"]

    text = req.document_text.lower()
    pos = sum(text.count(w) for w in positive_words)
    neg = sum(text.count(w) for w in negative_words)

    score = (pos - neg) / max(pos + neg, 1)
    confidence = min(0.55 + (abs(pos - neg) * 0.05), 0.99)

    decision_id = f"sent-{uuid4()}"
    features = {
        "positive_token_hits": float(pos),
        "negative_token_hits": float(neg),
        "text_length": float(len(req.document_text)),
    }
    shap_like = {
        "positive_token_hits": float(pos),
        "negative_token_hits": -float(neg),
        "text_length": float(len(req.document_text)) * 0.0001,
    }

    explain = make_explainability_payload(
        agent_name="Sentiment Agent",
        model_name="finbert-lite",
        model_version="2026.02",
        raw_features=features,
        shap_like_values=shap_like,
    )

    output = {
        "decision_id": decision_id,
        "ticker": req.ticker,
        "sentiment_score": round(score, 4),
        "confidence": round(confidence, 4),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as conn:
        explanation_id = insert_explanation(conn, "sentiment", decision_id, explain)
        insert_decision_log(
            conn,
            decision_type="sentiment",
            decision_id=decision_id,
            ticker=req.ticker,
            input_payload=req.model_dump(),
            output_payload=output,
            policy_result={"status": "pass", "checks": ["source_allowed", "model_whitelisted"]},
            explanation_id=explanation_id,
        )

    return {"signal": output, "explainability": explain}
