from __future__ import annotations

from typing import Any


def normalize_contributions(features: dict[str, float]) -> dict[str, float]:
    total = sum(abs(v) for v in features.values()) or 1.0
    return {k: round(v / total, 6) for k, v in features.items()}


def build_explanation_text(agent_name: str, features: dict[str, float]) -> str:
    sorted_items = sorted(features.items(), key=lambda x: abs(x[1]), reverse=True)
    top = ", ".join(f"{k}={v:.4f}" for k, v in sorted_items[:3])
    return f"{agent_name} decision driven primarily by: {top}."


def make_explainability_payload(
    agent_name: str,
    model_name: str,
    model_version: str,
    raw_features: dict[str, float],
    shap_like_values: dict[str, float],
) -> dict[str, Any]:
    normalized = normalize_contributions(shap_like_values)
    return {
        "model_name": model_name,
        "model_version": model_version,
        "feature_attributions": raw_features,
        "shap_summary": normalized,
        "explanation_text": build_explanation_text(agent_name, shap_like_values),
    }
