from io import BytesIO
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.contracts import EvidenceNode, EvidenceEdge
from core.evidence_graph import EvidenceGraph
from agents.rule_agent import RuleAgent


STATE_INIT = "STATE_INIT"
STATE_FINAL_VERDICT = "STATE_FINAL_VERDICT"
STATE_ROLLBACK_REVIEW = "STATE_ROLLBACK_REVIEW"

CONSISTENCY_THRESHOLD = 0.80
latest_audit_run: dict[str, Any] | None = None

app = FastAPI(title="AuditCore API", version="1.0.0")

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


@app.post("/api/audit")
async def run_audit(file: UploadFile = File(...)):
    global latest_audit_run

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

    rule_agent = RuleAgent()
    rule_findings = rule_agent.scan(df)
    scan_result = rule_agent.build_scan_result(df)

    graph = EvidenceGraph()
    for i, finding in enumerate(rule_findings):
        graph.add_node(
            EvidenceNode(
                node_id=f"rule_fact_{i}",
                node_type="RuleFinding",
                content=finding.summary,
            )
        )

    global_consistency_score = graph.calculate_consistency_score()

    if global_consistency_score >= CONSISTENCY_THRESHOLD:
        current_state = STATE_FINAL_VERDICT
    else:
        current_state = STATE_ROLLBACK_REVIEW

    nodes_data = [
        {
            "node_id": nid,
            "node_type": node.node_type,
            "content": node.content,
        }
        for nid, node in graph.nodes.items()
    ]

    edges_data = [
        {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation": edge.relation,
            "weight": edge.weight,
        }
        for edge in graph.edges
    ]

    stats = scan_result["stats"]

    audit_result = {
        "global_consistency_score": round(global_consistency_score, 4),
        "current_state": current_state,
        "consistency_threshold": CONSISTENCY_THRESHOLD,
        "stats": {
            "total_records": stats["total_records"],
            "anomaly_count": stats["anomaly_count"],
            "max_amount": stats["max_amount"],
        },
        "rule_findings": [
            {
                "label": f.label,
                "record_count": f.record_count,
                "summary": f.summary,
            }
            for f in rule_findings
        ],
        "graph": {
            "nodes": nodes_data,
            "edges": edges_data,
        },
    }

    latest_audit_run = {
        "fileName": file.filename,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
        "auditData": audit_result,
    }

    return audit_result


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000)
