# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AuditCore is an AI-powered multi-agent audit collaboration platform. It ingests Excel financial data, runs rule-based anomaly detection, then orchestrates multiple LLM agents (Junior Auditor, Challenger, Fact Checker, Senior Partner) to debate and arbitrate audit findings. The output is structured audit working papers with evidence graphs and consistency scores.

## Commands

### Backend (Python)
```bash
pip install -r requirements.txt   # Install dependencies
python server.py                   # Start API server on http://127.0.0.1:8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev      # Dev server on http://localhost:3000
npm run build    # Production build
npm run lint     # ESLint
```

No test infrastructure or CI/CD exists in this repo.

## Architecture

### Backend (`server.py`, `core/`, `agents/`)

**server.py** — FastAPI entry point with CORS for `localhost:3000`. Three routes:
- `POST /api/audit` — accepts `.xlsx` upload, runs the full audit pipeline, returns structured result
- `GET /api/audit/latest` — returns the most recent audit (in-memory global, lost on restart)
- `GET /api/health` — health check

**core/contracts.py** — Data contracts as dataclasses: `RuleFinding`, `FactCheckResult`, `EvidenceNode`, `EvidenceEdge`, `DraftWorkpaper`. All inter-agent data flows through these types.

**core/evidence_graph.py** — `EvidenceGraph` stores audit evidence as a directed graph. Consistency score formula: `(support_sum - conflict_sum) / total_edges`. Exports Markdown working papers.

**core/rag_engine.py** — `AuditKnowledgeBase` for PDF ingestion into ChromaDB using `shibing624/text2vec-base-chinese` embeddings (HuggingFace).

**core/data_loader.py** — `AuditDataLoader` for Excel loading and basic anomaly scanning.

**agents/** — Each agent wraps an OpenAI-compatible LLM call:
1. `rule_agent.py` — deterministic scanning (negative amounts, duplicates)
2. `auditor_agent.py` — LLM-generated preliminary audit report
3. `challenger_agent.py` — independent rebuttal of the junior's findings
4. `fact_check_agent.py` — evidence-level verification + conflict resolution
5. `senior_partner_agent.py` — final arbitration verdict

### Frontend (`frontend/app/`)

Three pages:
- `/` (Console) — drag-and-drop `.xlsx` upload, metric cards, verdict banner, findings table
- `/arena` (Agent Arena) — multi-agent council visualization with collaboration timeline
- `/papers` (Working Papers) — auto-generated Markdown audit papers with copy/download

i18n: Chinese/English via React context in `app/i18n/`, persisted to localStorage.

### LLM Routing

Agents use an OpenAI-compatible client. When `api_base` contains `localhost`, the model defaults to `llama3:8b` (Ollama); otherwise `gpt-4o-mini`. Configuration via `.env` (`OPENAI_API_KEY`, `OPENAI_BASE_URL`).

## Key Conventions

- Backend uses Python dataclasses for all structured data (not Pydantic models)
- The `streamlit` dependency in `requirements.txt` is a leftover from a previous UI framework and is not imported anywhere
- Frontend uses Tailwind CSS v4 (PostCSS plugin, not the v3 config file approach)
- The `frontend/CLAUDE.md` contains Next.js-specific agent rules — consult it for frontend changes
