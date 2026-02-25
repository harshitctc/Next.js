# Agentic Finance Platform Architecture (SEC/FINRA-Aligned)

## 1) System Architecture Diagram

```mermaid
flowchart LR
    subgraph Clients
      PM[Portfolio Manager UI]
      COMP[Compliance Console]
      OMS[Order Management System]
    end

    PM --> GW
    COMP --> GW
    OMS --> GW

    subgraph API Gateway Layer
      GW[FastAPI Gateway + Policy Engine\nService Router + Vendor Abstraction]
      REG[Reg BI Decision Logger]
    end

    GW --> REG

    subgraph AI/Agent Services
      SA[Sentiment Agent\nNews + Filings NLP]
      PA[Portfolio Agent\nTwo-Tower Allocation]
      RA[Risk Agent\nVaR + Drift Monitor]
      EXPL[Explainability Service\nSHAP + Feature Attribution]
    end

    GW --> SA
    GW --> PA
    GW --> RA

    SA --> EXPL
    PA --> EXPL
    RA --> EXPL

    subgraph Data Plane
      PG[(PostgreSQL + pgvector)]
      BUS[(Kafka/Redpanda Event Bus)]
      FS[(SEC Filings / News Feeds)]
      MKT[(Market Data Streams)]
      FEAT[(Feature Store)]
    end

    FS --> SA
    MKT --> PA
    MKT --> RA
    FEAT --> PA

    SA --> PG
    PA --> PG
    RA --> PG
    EXPL --> PG

    SA --> BUS
    PA --> BUS
    RA --> BUS

    subgraph Controls
      AUDIT[Immutable Audit Trail]
      ALERT[Drift & Breach Alerts]
      RBAC[RBAC + Entitlements]
    end

    REG --> AUDIT
    RA --> ALERT
    GW --> RBAC
```

## 2) Control and Compliance Design Notes

- **Reg BI explainability:** every recommendation or risk action persists feature attributions and rationale text in `explanations` and `decision_logs`.
- **Vendor lock-in prevention:** gateway routes through a provider interface (`OpenAI`, `Anthropic`, local `vLLM`) selected by policy and can be hot-swapped without downstream changes.
- **Supervisory controls:** all agent outputs are evented and logged with model version, confidence, and human override metadata.

## 3) Agent Orchestration Pattern

1. Ingest market/news/filings payload.
2. Run model inference.
3. Compute explainability artifacts (SHAP/feature contribution).
4. Evaluate policy thresholds (risk, concentration, drift).
5. Persist decision + explanations + policy outcome.
6. Emit event to bus for downstream execution/monitoring.
