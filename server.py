from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.contracts import AgentResult, AuditPipelineResult
from core.orchestrator import AuditOrchestrator

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
AUDIT_LANG = os.getenv("AUDIT_LANG", "中文")
CONSISTENCY_THRESHOLD = float(os.getenv("CONSISTENCY_THRESHOLD", "0.80"))

latest_audit_run: dict[str, Any] | None = None
latest_arena_data: dict[str, Any] | None = None

app = FastAPI(title="AuditCore API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AuditCore API"}


@app.get("/api/audit/latest")
async def get_latest_audit():
    if latest_audit_run is None:
        return {"error": "No audit file has been uploaded yet."}
    return latest_audit_run


@app.get("/api/audit/latest/arena")
async def get_latest_arena():
    if latest_arena_data is None:
        return {"error": "No audit file has been uploaded yet."}
    return latest_arena_data


@app.post("/api/audit")
async def run_audit(file: UploadFile = File(...)):
    global latest_audit_run, latest_arena_data

    if not file.filename or not file.filename.endswith(".xlsx"):
        return {"error": "Only .xlsx files are accepted"}

    contents = await file.read()

    try:
        df = pd.read_excel(BytesIO(contents), engine="openpyxl")
    except Exception as e:
        return {"error": f"Failed to read Excel file: {e}"}

    if df.empty:
        return {"error": "The uploaded file contains no data."}

    amount_candidates = ["data", "Amount", "金额", "数值"]
    for candidate in amount_candidates:
        if candidate in df.columns:
            if candidate != "Amount":
                df = df.rename(columns={candidate: "Amount"})
            break

    if not OPENAI_API_KEY:
        return _run_fallback_rule_only(df, file.filename)

    try:
        orchestrator = AuditOrchestrator(
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_BASE_URL,
            lang=AUDIT_LANG,
            threshold=CONSISTENCY_THRESHOLD,
        )
        result: AuditPipelineResult = orchestrator.run_pipeline(df)
    except Exception as e:
        return {"error": f"Pipeline execution failed: {e}"}

    # 向后兼容：构造 Dashboard 页面所需的 auditData 格式
    audit_result = {
        "global_consistency_score": result.global_consistency_score,
        "current_state": result.current_state,
        "consistency_threshold": result.consistency_threshold,
        "stats": result.stats,
        "rule_findings": result.rule_findings,
        "graph": result.evidence_graph_snapshot,
    }

    now = datetime.now(timezone.utc).isoformat()

    latest_audit_run = {
        "fileName": file.filename,
        "uploadedAt": now,
        "auditData": audit_result,
    }

    # Arena 页面所需的完整数据
    latest_arena_data = _build_arena_response(result, file.filename, now)

    return audit_result


def _run_fallback_rule_only(df: pd.DataFrame, filename: str) -> dict[str, Any]:
    """当 API Key 未配置时，仅运行规则扫描（向后兼容）。"""
    global latest_audit_run, latest_arena_data
    from agents.rule_agent import RuleAgent
    from core.evidence_graph import EvidenceGraph
    from core.contracts import EvidenceNode

    rule_agent = RuleAgent()
    rule_findings = rule_agent.scan(df)
    scan_result = rule_agent.build_scan_result(df)

    graph = EvidenceGraph()
    for i, finding in enumerate(rule_findings):
        graph.add_node(EvidenceNode(
            node_id=f"rule_fact_{i}",
            node_type="RuleFinding",
            content=finding.summary,
        ))

    score = graph.calculate_consistency_score()
    stats = scan_result["stats"]
    nodes_data = [{"node_id": n.node_id, "node_type": n.node_type, "content": n.content} for n in graph.nodes.values()]
    edges_data = [{"source_id": e.source_id, "target_id": e.target_id, "relation": e.relation, "weight": e.weight} for e in graph.edges]

    audit_result = {
        "global_consistency_score": round(score, 4),
        "current_state": "STATE_FINAL_VERDICT" if score >= CONSISTENCY_THRESHOLD else "STATE_ROLLBACK_REVIEW",
        "consistency_threshold": CONSISTENCY_THRESHOLD,
        "stats": {"total_records": stats["total_records"], "anomaly_count": stats["anomaly_count"], "max_amount": stats["max_amount"]},
        "rule_findings": [{"label": f.label, "record_count": f.record_count, "summary": f.summary} for f in rule_findings],
        "graph": {"nodes": nodes_data, "edges": edges_data},
    }

    now = datetime.now(timezone.utc).isoformat()
    latest_audit_run = {"fileName": filename, "uploadedAt": now, "auditData": audit_result}
    return audit_result


def _build_arena_response(
    result: AuditPipelineResult, filename: str, uploaded_at: str
) -> dict[str, Any]:
    """将 AuditPipelineResult 转换为前端 Arena 页面所需的完整数据结构。"""
    agent_map = {}
    for ar in result.agent_results:
        agent_map[ar.agent_id] = ar

    # 构造 agent 角色列表
    agents = []
    role_config = [
        ("junior_agent", "junior", "Junior Auditor"),
        ("challenger_agent", "challenger", "Challenger Auditor"),
        ("fact_check_agent", "factCheck", "Fact Check Agent"),
        ("senior_partner_agent", "partner", "Senior Partner"),
    ]
    for agent_id, role_id, default_title in role_config:
        ar = agent_map.get(agent_id)
        if ar:
            agents.append({
                "id": role_id,
                "title": default_title,
                "status": ar.status,
                "confidence": ar.confidence,
                "output": ar.output,
                "evidence_node_ids": ar.evidence_node_ids,
            })

    # 构造时间线
    timeline = []
    for i, transition in enumerate(result.state_history):
        timeline.append({
            "stage": f"{i+1:02d}",
            "title": transition.get("to", ""),
            "description": transition.get("reason", ""),
            "score": transition.get("score", 0),
        })

    # 最终裁决
    senior_output = agent_map.get("senior_partner_agent", AgentResult(agent_id="", status="skipped")).output
    final_decision = {
        "final_verdict": senior_output.get("final_verdict", "Unknown"),
        "final_risk_score": senior_output.get("final_risk_score", 0),
        "reasoning": senior_output.get("reasoning", ""),
        "action_item": senior_output.get("action_item", ""),
    }

    return {
        "caseId": f"AC-{uploaded_at.replace('-', '').replace(':', '').replace('T', '')[:14]}",
        "fileName": filename,
        "uploadedAt": uploaded_at,
        "metrics": {
            "total_records": result.stats.get("total_records", 0),
            "anomaly_count": result.stats.get("anomaly_count", 0),
            "exposure_amount": result.stats.get("max_amount", 0),
            "consistency_score": result.global_consistency_score,
            "rollback_count": result.rollback_count,
        },
        "agents": agents,
        "timeline": timeline,
        "evidence": result.evidence_graph_snapshot,
        "finalDecision": final_decision,
        "localSubgraphScores": result.local_subgraph_scores,
        "stateHistory": result.state_history,
        "workpaperMarkdown": result.workpaper_markdown,
        "privacyLog": result.privacy_log,
    }


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000)
