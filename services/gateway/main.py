from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="agentic-gateway", version="0.1.0")


class RouteRequest(BaseModel):
    service: str
    payload: dict[str, Any]


SERVICE_URLS = {
    "sentiment": os.getenv("SENTIMENT_URL", "http://sentiment-agent:8001/agent/run"),
    "portfolio": os.getenv("PORTFOLIO_URL", "http://portfolio-agent:8002/agent/run"),
    "risk": os.getenv("RISK_URL", "http://risk-agent:8003/agent/run"),
}

LLM_PROVIDER_MAP = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet",
    "local_vllm": "mistral-7b-instruct",
}


@app.get("/providers")
def providers() -> dict[str, str]:
    return LLM_PROVIDER_MAP


@app.post("/route")
async def route(req: RouteRequest) -> dict:
    if req.service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Unknown service: {req.service}")

    target = SERVICE_URLS[req.service]
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(target, json=req.payload)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {
        "service": req.service,
        "target": target,
        "provider": os.getenv("ACTIVE_LLM_PROVIDER", "openai"),
        "result": response.json(),
    }
