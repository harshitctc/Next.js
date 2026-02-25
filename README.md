# Agentic Finance Platform (FastAPI Microservices Boilerplate)

This repository includes:
- A microservices architecture for sentiment, portfolio allocation, and risk monitoring.
- A PostgreSQL + pgvector schema for signals, decisions, and explainability artifacts.
- An API Gateway that enables service/provider swapping to reduce LLM vendor lock-in.

## Services
- `services/sentiment_agent/main.py`
- `services/portfolio_agent/main.py`
- `services/risk_agent/main.py`
- `services/gateway/main.py`

## Core Design Requirements Covered
- **SEC/FINRA posture:** immutable decision logs with model metadata and policy checks.
- **Reg BI explainability:** every decision generates feature attribution payloads.
- **pgvector support:** embeddings stored on `documents` and tower embeddings in `portfolio_snapshots`.

## Run locally
```bash
pip install -r requirements.txt
uvicorn services.sentiment_agent.main:app --port 8001
uvicorn services.portfolio_agent.main:app --port 8002
uvicorn services.risk_agent.main:app --port 8003
uvicorn services.gateway.main:app --port 8000
```

## Database
Apply `db/schema.sql` to a PostgreSQL instance with pgvector enabled.

## Architecture
See `docs/architecture.md` for the Mermaid system diagram and orchestration flow.
