<div align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="Version 2.0.0">
  <img src="https://img.shields.io/badge/python-3.10%2B-brightgreen" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Next.js-16-black" alt="Next.js 16">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/status-active--development-yellow" alt="Active Development">

  <h1>🏛️ AuditCore</h1>
  <p><strong>AI-Powered Multi-Agent Audit Collaboration Platform</strong></p>
  <p><em>专利级多智能体审计业务流程模拟系统</em></p>
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Pipeline Flow](#-pipeline-flow)
- [LLM Agent Council](#-llm-agent-council)
- [Evidence Graph & Consistency Scoring](#-evidence-graph--consistency-scoring)
- [Privacy Layer](#-privacy-layer)
- [RAG Knowledge Base](#-rag-knowledge-base)
- [Multi-Provider LLM Routing](#-multi-provider-llm-routing)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Frontend Pages](#-frontend-pages)
- [Project Structure](#-project-structure)
- [Patent & Research](#-patent--research)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 Overview

**AuditCore** is an advanced AI-powered audit collaboration platform that simulates a complete **virtual audit firm workflow**. It ingests financial data from Excel spreadsheets, runs rule-based anomaly detection, then orchestrates a **council of LLM-powered agents** — Junior Auditor, Challenger, Fact Checker, and Senior Partner — to debate, verify, and arbitrate audit findings.

The system uses a **patent-pending evidence graph with consistency scoring** and a **DAG-driven state machine** to control the multi-agent pipeline, enabling automatic conflict detection, evidence rollback, and convergence guarantee. The output is a structured audit working paper with evidence traceability, consistency metrics, and final arbitration verdicts.

> **🎯 Target Users**: Auditors, accounting firms, financial regulators, researchers in AI-driven audit automation, and enterprises seeking to automate internal audit processes.

---

## 🚀 Key Features

### 🤖 Multi-Agent Audit Council
- **Junior Auditor** — Generates preliminary audit reports and risk assessments
- **Challenger Auditor** — Independently reviews and rebuts findings with skeptical analysis
- **Fact Checker** — Verifies evidence and quantifies support/conflict scores
- **Senior Partner** — Issues final arbitration verdicts with actionable recommendations

### 📊 Evidence Graph with Consistency Scoring
- All agent outputs mapped as a **directed evidence graph**
- **Consistency score formula**: `(Σ support - Σ conflict) / |E|` — quantifies agreement across agents
- **Local subgraph scoring** for fine-grained quality assessment per pipeline stage
- **Automatic rollback** when consistency falls below threshold

### 🔄 DAG-Driven State Machine
- 9-state pipeline with deterministic transitions
- **Consistency-gated branching**: low scores trigger conflict resolution + local rollback
- **Convergence guarantee**: max iteration limit with improvement detection prevents infinite loops
- Full state history tracking for audit trail

### 🔐 Privacy Layer
- Automatic detection of sensitive columns (names, IDs, account numbers)
- Reversible pseudonymization (`PERSON_0001`, `ACCT_0001`)
- Full privacy audit log documenting all transformations
- Automated restoration in final output

### 🔌 Multi-Provider LLM Routing
- **7 providers** supported: OpenAI, DeepSeek, Moonshot, Qwen (通义千问), SiliconFlow, Ollama (local), Anthropic (Claude)
- **Per-agent model assignment** — mix providers in one pipeline (e.g., GPT-4o for Junior, Claude for Partner)
- Runtime reconfiguration via Settings UI without server restart

### 🌐 Full i18n Support
- Chinese and English UI (React context + localStorage persistence)
- Auto-detects system language on first visit
- Backend audit language independently configurable via `AUDIT_LANG`

### 🧠 RAG-Enhanced Audit Knowledge
- PDF ingestion into ChromaDB vector store
- Chinese-optimized embeddings (`shibing624/text2vec-base-chinese`)
- Semantic retrieval of audit rules and regulations

### 📑 Automated Working Papers
- Structured Markdown audit working paper generation
- Evidence graph export with node/edge relationship visualization
- Copy-to-clipboard and `.md` file download

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Next.js 16 Frontend                          │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│   │ Console  │  │  Arena   │  │  Papers  │  │   Settings       │  │
│   │ Dashboard│  │Agent Viz │  │Working   │  │  Model Config    │  │
│   │ Upload   │  │Timeline  │  │Papers    │  │  Per-Agent       │  │
│   │ Metrics  │  │Evidence  │  │Markdown  │  │  Override        │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│        └──────────────┴─────────────┴─────────────────┘             │
│                           │ HTTP/JSON                               │
│                           │ CORS (localhost:3000)                    │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────┐
│                     FastAPI Backend (port 8000)                      │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    Model Registry                            │  │
│   │  7 Providers · Per-Agent Overrides · Runtime Reconfig        │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              DAG State Machine & Orchestrator                │  │
│   │   ┌─────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐ │  │
│   │   │ Rule    │→ │ Privacy    │→ │ Junior   │→ │Challenger│ │  │
│   │   │ Agent   │  │ Layer      │  │ Auditor  │  │ Auditor  │ │  │
│   │   └─────────┘  └────────────┘  └──────────┘  └──────────┘ │  │
│   │                                                             │  │
│   │   ┌──────────┐  ┌──────────────┐ ┌───────────┐  ┌────────┐ │  │
│   │   │FactCheck │→ │ Consistency  │→│Senior     │→ │Working │ │  │
│   │   │          │  │ Evaluation   │ │Partner    │  │Papers  │ │  │
│   │   └──────────┘  └──────┬───────┘ └───────────┘  └────────┘ │  │
│   │                         │ ↓ threshold?                      │  │
│   │                         │ → Conflict Resolution & Rollback  │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│   │   Evidence Graph        │  │   Privacy Layer             │   │
│   │   · Directed Graph      │  │   · Entity Detection        │   │
│   │   · Consistency Score   │  │   · Reversible Anonymization│   │
│   │   · Local Subgraph Eval │  │   · Restoration + Log       │   │
│   │   · Rollback Support    │  │                             │   │
│   └─────────────────────────┘  └─────────────────────────────┘   │
│                                                                     │
│   ┌─────────────────────────┐                                      │
│   │   RAG Engine            │                                      │
│   │   · ChromaDB Vector Store│                                     │
│   │   · PDF Ingestion       │                                      │
│   │   · Semantic Retrieval  │                                      │
│   └─────────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Flow

The pipeline is driven by a **DAG (Directed Acyclic Graph) State Machine** with 9 states. The consistency score serves as the primary control signal for state transitions.

```
STATE_INIT
    │
    ▼
STATE_RULE_SCAN ────────────────── Rule Agent (deterministic scan)
    │
    ▼
STATE_PRIVACY_ANONYMIZE ────────── Privacy Layer (entity masking)
    │
    ▼
STATE_JUNIOR_AUDIT ─────────────── Junior Auditor (LLM)
    │
    ▼
STATE_CHALLENGER_REVIEW ────────── Challenger Auditor (LLM)
    │
    ▼
STATE_FACT_CHECK ───────────────── Fact Checker (LLM)
    │
    ▼
STATE_CONSISTENCY_EVAL ─────────── Evidence Graph scoring
    │
    ├── Score ≥ Threshold (0.80) ───────────────► STATE_SENIOR_PARTNER
    │
    └── Score < Threshold & iter < max ─────────► STATE_CONFLICT_RESOLUTION
                                                          │
                                                          ▼
                                                  STATE_LOCAL_ROLLBACK
                                                          │
                                                          ▼
                                                  STATE_JUNIOR_AUDIT (retry)
    │
    └── Max iterations / not improving ─────────► STATE_SENIOR_PARTNER (forced)
                                                          │
                                                          ▼
                                                  STATE_WORKPAPER_GENERATION
                                                          │
                                                          ▼
                                                  STATE_FINAL_VERDICT (terminal)
```

### Rollback Mechanism

When the **global consistency score** falls below the configurable threshold (default: 0.80):

1. **Conflict Resolution** — The Fact Checker analyzes all conflict edges and attempts resolution
2. **Local Subgraph Scoring** — Each pipeline stage's subgraph is scored independently
3. **Targeted Rollback** — The subgraph with the lowest local score is removed entirely
4. **Re-execution** — The pipeline resumes from the Junior Auditor stage
5. **Convergence Protection** — Max 3 iterations; if scores stop improving, forced arbitration

This **local rollback** approach is significantly more efficient than restarting the entire pipeline.

---

## 🤖 LLM Agent Council

Each agent in the council plays a distinct role in the audit process:

### 1. 🔍 Rule Agent (Deterministic)
- **No LLM required** — runs offline with no API key
- Scans for: **negative amounts**, **duplicate rows**
- Outputs: structured `RuleFinding[]` with labels, counts, and summaries
- **Always available** as fallback when no API key is configured

### 2. 📝 Junior Auditor (LLM-Powered)
- **Prompt**: Anomaly data + statistical overview + auditor persona prompt
- **Output**: Natural language analysis + risk score (0–100)
- **Confidence**: Derived from risk score extremity (distance from 50)
- **Evidence**: Writes `junior_conclusion` node to evidence graph

### 3. ⚡ Challenger Auditor (LLM-Powered)
- **Role**: Independent skeptic — reviews the Junior's work
- **Prompt**: Same anomaly data + Junior's report + score
- **Output**: Rebuttal analysis + adjusted risk score (0–100)
- **Edge**: Creates `support` or `conflict` edge to Junior based on score divergence
  - Score difference > 20 points → `conflict` edge
  - Score difference ≤ 20 points → `support` edge

### 4. ✅ Fact Checker (LLM-Powered)
- **Role**: Evidence-level verification
- **Prompt**: Anomaly data + draft report + risk score
- **Output**: Analysis + support score (0.0–1.0) + conflict score (0.0–1.0)
- **Dual Edge Creation**: Can simultaneously create both `support` and `conflict` edges to Junior
- **Conflict Resolution**: Special method to analyze and resolve conflict edges between agents

### 5. 👑 Senior Partner (LLM-Powered)
- **Role**: Final arbitrator — reviews all prior work
- **Input**: Full context from all preceding agents
- **Output**:
  - `final_verdict`: `"True Anomaly"` or `"False Positive"`
  - `final_risk_score`: 0–100
  - `reasoning`: Detailed arbitration rationale
  - `action_item`: Recommended next steps
- **Evidence**: Writes `senior_partner_verdict` node with edges from all preceding conclusions

---

## 📈 Evidence Graph & Consistency Scoring

The **patent-pending core** of AuditCore. All agent outputs are mapped into a directed evidence graph that drives the entire pipeline.

### Graph Structure

```
                  ┌──────────────────────────────────┐
                  │         Evidence Graph            │
                  │                                   │
                  │   ┌──────────────┐                │
                  │   │ Rule Finding │                │
                  │   │  (fact_0)    │                │
                  │   └──────┬───────┘                │
                  │          │ support (0.7)          │
                  │          ▼                        │
                  │   ┌──────────────┐                │
                  │   │    Junior    │◄──── conﬂict ──│──┐
                  │   │  Conclusion  │                │  │
                  │   └──────┬───────┘                │  │
                  │          │ support (0.8)          │  │
                  │          ▼                        │  │
                  │   ┌──────────────┐   ┌──────────┐ │  │
                  │   │    Senior    │   │Challenger│─┘  │
                  │   │   Verdict    │   │Conclusion│    │
                  │   └──────────────┘   └──────────┘    │
                  │                                   │
                  │   ┌──────────────┐                │
                  │   │Fact Check    │ (dual edges)   │
                  │   │  Result      │                │
                  │   └──────────────┘                │
                  └──────────────────────────────────┘
```

### Consistency Score Formula

```
ConsistencyScore(G) = (Σ support_edge_weights - Σ conflict_edge_weights) / |E|
```

- **Range**: [-1.0, 1.0]
- **1.0**: Perfect agreement (no edges, or all edges are support)
- **0.0**: Balanced support and conflict
- **-1.0**: Complete disagreement
- **Threshold**: Configurable (default 0.80)

### Local Subgraph Scoring

Each pipeline stage produces a **subgraph** (identified by `subgraph_id`):
- `rule_scan`, `junior_audit`, `challenger_review`, `fact_check`, `senior_partner`

Local scores are calculated by considering only edges where **both endpoints** belong to the same subgraph. This enables:
- Per-stage quality assessment
- Targeted rollback to the worst-performing stage
- Fine-grained pipeline diagnostics

---

## 🔐 Privacy Layer

AuditCore includes a built-in **reversible anonymization layer** to protect sensitive data before it reaches LLM providers.

### How It Works

1. **Detection**: Scans DataFrame columns for sensitive identifiers
   - Names: `姓名`, `人员`, `vendor`, `供应商`, `company`, `公司`
   - Account IDs: `账号`, `身份证`, `id_number`, `account`
2. **Anonymization**: Replaces detected entities with pseudonyms
   - `张三` → `PERSON_0001`
   - `ACCT-12345` → `ACCT_0001`
3. **Isolation**: Amount columns and non-sensitive data pass through unchanged
4. **Restoration**: After pipeline completion, all pseudonyms are reversed in:
   - Working paper Markdown
   - Evidence graph node content
5. **Audit Trail**: A complete privacy transformation log is generated

> **Why this matters**: Sending financial data with personal identifiable information (PII) to third-party LLM APIs poses compliance risks. The privacy layer ensures no PII leaves your environment, while preserving the analytical value of the data.

---

## 📚 RAG Knowledge Base

AuditCore includes a **Retrieval-Augmented Generation (RAG)** engine for incorporating external audit knowledge:

- **Vector Store**: ChromaDB (persistent, filesystem-based)
- **Embeddings**: `shibing624/text2vec-base-chinese` (HuggingFace, Chinese-optimized)
- **Ingestion**: PDF documents from `knowledge_base/` directory
- **Chunking**: RecursiveCharacterTextSplitter (800 chars, 120 overlap)
- **Retrieval**: `retrieve_rules(query, top_k=2)` — semantic search over ingested regulations

> **🔮 Planned Enhancement**: RAG-augmented agents that retrieve relevant audit rules before generating responses, reducing hallucination and grounding outputs in authoritative sources.

---

## 🔌 Multi-Provider LLM Routing

AuditCore supports **7 LLM providers** with **per-agent model assignment** and **runtime reconfiguration**.

### Supported Providers

| Provider | Default Base URL | Default Model |
|----------|-----------------|---------------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Moonshot (月之暗面)** | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| **Qwen (通义千问)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| **SiliconFlow** | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V3` |
| **Ollama (Local)** | `http://localhost:11434/v1` | `llama3:8b` |
| **Anthropic (Claude)** | `https://api.anthropic.com` | `claude-sonnet-4-20250514` |

### Per-Agent Configuration

Each agent can be assigned a **different provider and model** independently:

```yaml
Junior Auditor:  DeepSeek Chat (cost-efficient draft)
Challenger:      GPT-4o (skeptical analysis)
Fact Checker:    Claude Sonnet (nuanced verification)
Senior Partner:  GPT-4o or Claude (final arbitration)
```

Configure via:
1. **Settings UI** — Runtime configuration in the frontend
2. **Environment variables** — `.env` file for persistent setup
3. **API endpoint** — `PUT /api/models` for programmatic control

---

## 🛠 Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI + Uvicorn |
| **LLM Client** | OpenAI Python SDK + Anthropic Python SDK |
| **Data Processing** | Pandas + OpenPyXL |
| **Vector Store** | ChromaDB (LangChain integration) |
| **Embeddings** | HuggingFace Transformers (`shibing624/text2vec-base-chinese`) |
| **PDF Processing** | PyPDF |
| **Config** | python-dotenv |

### Frontend
| Component | Technology |
|-----------|-----------|
| **Framework** | Next.js 16 (App Router) |
| **UI Library** | React 19 |
| **Styling** | Tailwind CSS v4 (PostCSS plugin) |
| **Icons** | Lucide React |
| **Language** | TypeScript |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- (Optional) Ollama for local LLM inference, or API keys for any supported provider

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AuditCore.git
cd AuditCore

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment (edit .env or copy from .env.example)
# Minimal local setup (Ollama):
cp .env.example .env
# Edit .env — set LLM_PROVIDER=ollama, LLM_API_KEY=ollama
# Or set OPENAI_API_KEY=sk-... for OpenAI

# Start the API server
python server.py
```

The API server starts at `http://127.0.0.1:8000`. Health check: `GET /api/health`

### Frontend Setup

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend starts at `http://localhost:3000`.

### Your First Audit

1. Open `http://localhost:3000` in your browser
2. Prepare an `.xlsx` file with financial data (columns: `Amount`, optional `Data`)
3. Drag and drop the file onto the Console page
4. Watch the pipeline run across all 4 agents
5. Explore results in the Arena (agent visualization) and Papers (working papers) pages

### Run Without LLM (Rule-Only Mode)

No API key needed — the system falls back to deterministic rule scanning:
```bash
# Leave OPENAI_API_KEY and LLM_API_KEY empty in .env
# Start the server
python server.py
# Upload an .xlsx file — Rule Agent will scan for negative amounts and duplicates
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Global default provider |
| `LLM_API_KEY` | `ollama` | Global API key |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Global base URL |
| `LLM_MODEL` | `llama3:8b` | Global default model |
| `AUDIT_LANG` | `中文` | Backend audit language (`中文` / `English`) |
| `CONSISTENCY_THRESHOLD` | `0.80` | Evidence graph pass threshold |
| `JUNIOR_LLM_PROVIDER` | — | Per-agent override: Junior Auditor |
| `JUNIOR_LLM_API_KEY` | — | Per-agent override: Junior API key |
| `JUNIOR_LLM_BASE_URL` | — | Per-agent override: Junior base URL |
| `JUNIOR_LLM_MODEL` | — | Per-agent override: Junior model |
| *(Same pattern for `CHALLENGER_`, `FACTCHECK_`, `SENIOR_`)* | | |
| `OPENAI_API_KEY` | — | Legacy fallback (backward compat) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Legacy fallback (backward compat) |

### Frontend Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_AUDIT_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API URL |

---

## 📡 API Reference

### `GET /api/health`
Health check endpoint.

**Response:** `{"status": "ok", "service": "AuditCore API"}`

---

### `GET /api/models`
Returns current model configuration and available provider presets.

**Response (simplified):**
```json
{
  "config": {
    "default": { "provider": "openai", "model": "gpt-4o-mini" },
    "agents": {
      "junior": { "provider": "deepseek", "model": "deepseek-chat" },
      "challenger": null,
      "factcheck": null,
      "senior": null
    }
  },
  "providerPresets": { ... }
}
```

---

### `PUT /api/models`
Update model configuration at runtime.

**Request:**
```json
{
  "default": {
    "provider": "openai",
    "api_key": "sk-...",
    "base_url": "",
    "model": ""
  },
  "agents": {
    "junior": { "provider": "deepseek", "api_key": "sk-...", "base_url": "", "model": "deepseek-chat" },
    "challenger": null,
    "factcheck": null,
    "senior": null
  }
}
```

---

### `GET /api/audit/latest`
Retrieve the most recent audit result (in-memory, lost on server restart).

**Response:**
```json
{
  "fileName": "financial_2024.xlsx",
  "uploadedAt": "2026-05-31T13:35:00Z",
  "auditData": {
    "global_consistency_score": 0.85,
    "current_state": "STATE_FINAL_VERDICT",
    "consistency_threshold": 0.80,
    "stats": { "total_records": 100, "anomaly_count": 5, "max_amount": 50000 },
    "rule_findings": [
      { "label": "Negative Amounts", "record_count": 3, "summary": "..." }
    ],
    "graph": { "nodes": [...], "edges": [...] }
  }
}
```

---

### `GET /api/audit/latest/arena`
Retrieve arena-specific visualization data for the most recent audit.

**Response fields:** `caseId`, `fileName`, `uploadedAt`, `metrics`, `agents[]`, `timeline[]`, `evidence`, `finalDecision`, `localSubgraphScores`, `stateHistory`, `workpaperMarkdown`, `privacyLog`

---

### `POST /api/audit`
Upload an `.xlsx` file and execute the full audit pipeline.

**Request:** Multipart form — `file` field with `.xlsx` file.

**Response:** Same as `/api/audit/latest` audit data.

---

## 🖥 Frontend Pages

### 🎛 Console (`/`)
The main dashboard for audit operations:
- **File Upload**: Drag-and-drop interface for `.xlsx` files
- **Health Status**: Real-time backend connection indicator
- **Metric Cards**: Consistency score, scanned records, anomalies, exposure amount
- **Verdict Banner**: Pass/fail status based on consistency threshold
- **Findings Table**: Rule findings with labels, counts, summaries, and severity (High/Low)

### ⚔ Arena (`/arena`)
Multi-agent council visualization:
- **Agent Cards**: 4 agent panels with status, confidence scores, and output summaries
- **Collaboration Timeline**: 5-stage visual timeline from rule scan to arbitration
- **Evidence Graph**: Node cards with support/conflict edge visualization
- **Weight Bars**: Visual edge weight comparison
- **Agent Detail Panel**: Click to view full agent output
- **Final Decision Panel**: Verdict, risk score, reasoning, and action items
- **Technical Panel**: Rollback count, consistency metrics

### 📄 Working Papers (`/papers`)
Auto-generated audit documentation:
- **Structured Markdown**: Audit overview, scan results, findings, evidence nodes, conclusion
- **Two-Column Layout**: Findings/evidence on left, Markdown preview on right
- **Risk Classification**: High (≥5 anomalies), Medium (>0), Low (0)
- **Export**: Copy to clipboard or download as `.md` file

### ⚙ Settings (`/settings`)
Runtime LLM configuration:
- **Provider Pills**: 7 provider selector with visual icons
- **API Configuration**: API Key, Base URL, Model Name fields with auto-fill
- **Per-Agent Override**: Toggle and configure each agent independently
- **Save**: Applies changes via `PUT /api/models` — no server restart needed

---

## 📁 Project Structure

```
AuditCore/
│
├── server.py                      # FastAPI entry point (6 endpoints)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── .gitignore
├── CLAUDE.md                      # Project guidelines for AI coding
│
├── core/                          # Backend core modules
│   ├── contracts.py               # Data contracts (dataclasses)
│   ├── data_loader.py             # Excel loading & parsing
│   ├── evidence_graph.py          # ★ Patent-pending: evidence graph + scoring
│   ├── model_registry.py          # Multi-provider LLM registry
│   ├── orchestrator.py            # Multi-agent pipeline orchestration
│   ├── privacy_layer.py           # ★ Patent-pending: reversible anonymization
│   ├── rag_engine.py              # RAG knowledge base (ChromaDB)
│   ├── state_machine.py           # ★ Patent-pending: DAG state machine
│   └── utils.py                   # Path utilities
│
├── agents/                        # LLM agent implementations
│   ├── __init__.py
│   ├── base_agent.py              # Abstract base class with LLM routing
│   ├── rule_agent.py              # Deterministic rule scanner (no LLM)
│   ├── auditor_agent.py           # Junior Auditor (LLM)
│   ├── challenger_agent.py        # Challenger Auditor (LLM)
│   ├── fact_check_agent.py        # Fact Checker (LLM)
│   └── senior_partner_agent.py    # Senior Partner (LLM)
│
└── frontend/                      # Next.js 16 frontend
    ├── package.json
    ├── next.config.ts
    ├── postcss.config.mjs
    ├── tsconfig.json
    ├── eslint.config.mjs
    └── app/
        ├── layout.tsx             # Root server layout
        ├── client-layout.tsx      # Client layout + sidebar + i18n switcher
        ├── sidebar-nav.tsx        # Navigation sidebar
        ├── globals.css            # Tailwind v4 + custom animations
        ├── page.tsx               # Console dashboard (upload + metrics)
        ├── favicon.ico
        ├── i18n/
        │   ├── index.tsx          # React context i18n provider
        │   ├── zh.ts              # Chinese translations (~300 keys)
        │   └── en.ts              # English translations (~300 keys)
        ├── arena/
        │   └── page.tsx           # Agent Arena visualization
        ├── papers/
        │   └── page.tsx           # Working Papers (Markdown export)
        └── settings/
            └── page.tsx           # Model configuration UI
```

---

## 🧪 Patent & Research

AuditCore is built around a **Chinese invention patent application** titled:

> **"一种基于证据图一致性评分与状态机驱动的多智能体审计业务流程模拟方法及系统"**
> *(A method and system for multi-agent audit business process simulation based on evidence graph consistency scoring and state machine driving)*

### Patent Claims (Implemented)

| # | Claim | Implementation |
|---|-------|---------------|
| 1 | Multi-agent virtual audit council (Junior → Challenger → Fact Check → Senior) | `core/orchestrator.py` — full pipeline |
| 1c | Evidence graph consistency score → state transition control | `core/evidence_graph.py` — `calculate_consistency_score()` |
| 4 | Local subgraph rollback with worst-score targeting | `core/evidence_graph.py` — `remove_subgraph()`, `calculate_all_local_scores()` |
| 6 | Maximum iteration limit with convergence detection | `core/state_machine.py` — iteration tracking + improvement check |
| 8 | Conflict resolution → rollback → re-execution loop | `core/orchestrator.py` — `_run_conflict_resolution()` + `_run_local_rollback()` |
| 10 | Automated working paper generation with evidence chain | `core/evidence_graph.py` — `export_working_paper()` |

### Patent Strategy (4 Directions)

1. **🔵 Main Patent**: Multi-agent collaborative virtual audit group — **Highest priority**
2. **🟢 Sub-Patent**: Enhanced RAG with path optimization and node re-ranking
3. **🟡 Sub-Patent**: Anti-hallucination fact-checking with claim decomposition
4. **🔴 Defensive Patent**: Privacy anonymization layer for audit data

---

## 🗺 Roadmap

### ✅ Completed
- [x] Multi-agent LLM council (5 agents)
- [x] Evidence graph with consistency scoring
- [x] DAG state machine with rollback
- [x] Privacy anonymization layer
- [x] Multi-provider LLM routing (7 providers, per-agent override)
- [x] RAG knowledge base (ChromaDB + Chinese embeddings)
- [x] Frontend dashboard (4 pages)
- [x] Chinese/English i18n
- [x] Runtime model configuration

### 🔄 In Progress
- [ ] RAG-augmented agents (rule retrieval before LLM calls)
- [ ] Anti-hallucination fact checker with claim decomposition
- [ ] Docker deployment (docker-compose)
- [ ] Enhanced working paper templates

### 📅 Planned
- [ ] PDF audit report export (bilingual)
- [ ] Audit history persistence (SQLite/PostgreSQL)
- [ ] User authentication & multi-tenant support
- [ ] Real-time streaming agent output (Server-Sent Events)
- [ ] Comparative audit mode (run same data against multiple model configs)
- [ ] Custom rule engine (user-defined scan rules)
- [ ] CI/CD pipeline with automated testing
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Sample audit datasets for demo/evaluation

---

## 🤝 Contributing

Contributions are welcome! This project is in active development for both research and practical application.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

### Development Guidelines

- Backend: Python dataclasses for structured data (not Pydantic)
- Frontend: Tailwind CSS v4 (PostCSS plugin — not v3 config file)
- TypeScript: Strict mode enabled
- All LLM agent outputs should follow the standardized `AgentResult` contract

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

> **Note**: The patent-pending algorithms (evidence graph consistency scoring, DAG state machine with rollback, privacy layer) are part of an ongoing patent application. Academic and research use is encouraged; commercial use may require licensing.

---

<div align="center">
  <sub>Built with ❤️ for the future of AI-powered auditing</sub>
  <br>
  <sub>© 2026 AuditCore Project</sub>
</div>