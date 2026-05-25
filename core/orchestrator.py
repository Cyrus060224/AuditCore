# -*- coding: utf-8 -*-
"""
审计流水线编排器。

串联所有 Agent，驱动 DAG 状态机，构建证据图，
执行一致性评分驱动的冲突消解与局部回退，
最终生成结构化审计工作底稿。
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from agents.rule_agent import RuleAgent
from agents.auditor_agent import JuniorAuditorAgent
from agents.challenger_agent import ChallengerAgent
from agents.fact_check_agent import FactCheckAgent
from agents.senior_partner_agent import SeniorPartnerAgent
from core.contracts import (
    AgentResult,
    AuditPipelineResult,
    DraftWorkpaper,
    EvidenceEdge,
    EvidenceNode,
    FactCheckResult,
)
from core.evidence_graph import EvidenceGraph
from core.privacy_layer import PrivacyLayer
from core.state_machine import (
    DAGStateMachine,
    STATE_CONFLICT_RESOLUTION,
    STATE_CONSISTENCY_EVAL,
    STATE_FINAL_VERDICT,
    STATE_INIT,
    STATE_JUNIOR_AUDIT,
    STATE_LOCAL_ROLLBACK,
    STATE_RULE_SCAN,
    STATE_SENIOR_PARTNER,
    STATE_WORKPAPER_GENERATION,
)


class AuditOrchestrator:
    """
    多 Agent 审计流水线编排器。

    按 DAG 状态机驱动各 Agent，将输出映射至证据图，
    通过一致性评分控制状态转移与回退。
    """

    def __init__(
        self,
        api_key: str,
        api_base: str,
        lang: str = "English",
        threshold: float = 0.80,
        max_iterations: int = 3,
    ) -> None:
        self.lang = lang
        self.rule_agent = RuleAgent()
        self.junior_agent = JuniorAuditorAgent(lang=lang, api_key=api_key, api_base=api_base)
        self.challenger_agent = ChallengerAgent(lang=lang, api_key=api_key, api_base=api_base)
        self.fact_check_agent = FactCheckAgent(lang=lang, api_key=api_key, api_base=api_base)
        self.senior_partner_agent = SeniorPartnerAgent(lang=lang, api_key=api_key, api_base=api_base)
        self.privacy_layer = PrivacyLayer()
        self.graph = EvidenceGraph()
        self.state_machine = DAGStateMachine(threshold=threshold, max_iterations=max_iterations)
        self.agent_results: list[AgentResult] = []
        self._df: pd.DataFrame | None = None
        self._anomalies: dict = {}
        self._stats: dict = {}
        self._rule_findings: list = []
        self._junior_report: str = ""
        self._junior_score: int = 50
        self._challenger_rebuttal: str = ""
        self._challenger_score: int = 50

    def run_pipeline(self, df: pd.DataFrame) -> AuditPipelineResult:
        """
        执行完整审计流水线。

        流程由 DAG 状态机驱动：
        INIT → RULE_SCAN → PRIVACY → JUNIOR → CHALLENGER → FACT_CHECK
        → CONSISTENCY_EVAL → (通过/回退) → SENIOR_PARTNER → WORKPAPER → FINAL
        """
        self._df = df

        while not self.state_machine.is_terminal():
            state = self.state_machine.get_current_state()

            if state == STATE_INIT:
                self.state_machine.transition(1.0, 0)

            elif state == STATE_RULE_SCAN:
                self._run_rule_scan()
                self.state_machine.transition(1.0, 0)

            elif state == "STATE_PRIVACY_ANONYMIZE":
                self._run_privacy()
                self.state_machine.transition(1.0, 0)

            elif state == STATE_JUNIOR_AUDIT:
                self._run_junior_audit()
                self.state_machine.transition(1.0, 0)

            elif state == "STATE_CHALLENGER_REVIEW":
                self._run_challenger_review()
                self.state_machine.transition(1.0, 0)

            elif state == "STATE_FACT_CHECK":
                self._run_fact_check()
                self.state_machine.transition(1.0, 0)

            elif state == STATE_CONSISTENCY_EVAL:
                self._run_consistency_eval()

            elif state == STATE_CONFLICT_RESOLUTION:
                self._run_conflict_resolution()
                self.state_machine.transition(1.0, 0)

            elif state == STATE_LOCAL_ROLLBACK:
                self._run_local_rollback()
                self.state_machine.transition(1.0, 0)

            elif state == STATE_SENIOR_PARTNER:
                self._run_senior_partner()
                self.state_machine.transition(1.0, 0)

            elif state == STATE_WORKPAPER_GENERATION:
                self._run_workpaper_generation()
                self.state_machine.transition(1.0, 0)

            else:
                break

        return self._build_result()

    def _run_rule_scan(self) -> None:
        """步骤A：规则穿透 Agent 扫描。"""
        assert self._df is not None
        self._rule_findings = self.rule_agent.scan(self._df)
        scan_result = self.rule_agent.build_scan_result(self._df)
        self._anomalies = scan_result["anomalies"]
        self._stats = scan_result["stats"]

        node_ids = []
        for i, finding in enumerate(self._rule_findings):
            node_id = f"rule_fact_{i}"
            self.graph.add_node(EvidenceNode(
                node_id=node_id,
                node_type="RuleFinding",
                content=finding.summary,
                subgraph_id="rule_scan",
            ))
            node_ids.append(node_id)

        self.agent_results.append(AgentResult(
            agent_id="rule_agent",
            status="success",
            output={"findings": [{"label": f.label, "count": f.record_count, "summary": f.summary} for f in self._rule_findings]},
            evidence_node_ids=node_ids,
            confidence=1.0,
        ))

    def _run_privacy(self) -> None:
        """步骤A1：隐私脱敏层。"""
        assert self._df is not None
        self.privacy_layer.anonymize_dataframe(self._df)

    def _run_junior_audit(self) -> None:
        """步骤B：初审 Agent。"""
        result = self.junior_agent.run(self._anomalies, self._stats)
        self.agent_results.append(result)

        if result.status == "success":
            output = result.output
            self._junior_report = output.get("analysis", "")
            self._junior_score = int(output.get("risk_score", 50))

            self.graph.add_node(EvidenceNode(
                node_id="junior_conclusion",
                node_type="JuniorConclusion",
                content=self._junior_report,
                subgraph_id="junior_audit",
                confidence=result.confidence,
            ))

            # 规则发现 → 初审结论的边
            for node_id in result.evidence_node_ids:
                for rule_node in self.graph.get_nodes_by_subgraph("rule_scan"):
                    self.graph.add_edge(EvidenceEdge(
                        source_id=rule_node.node_id,
                        target_id="junior_conclusion",
                        relation="support",
                        weight=0.7,
                    ))

    def _run_challenger_review(self) -> None:
        """步骤B：复核 Agent。"""
        result = self.challenger_agent.run(
            self._anomalies, self._stats, self._junior_report, self._junior_score
        )
        self.agent_results.append(result)

        if result.status == "success":
            output = result.output
            self._challenger_rebuttal = output.get("rebuttal", "")
            self._challenger_score = int(output.get("adjusted_risk_score", 50))

            self.graph.add_node(EvidenceNode(
                node_id="challenger_conclusion",
                node_type="ChallengerConclusion",
                content=self._challenger_rebuttal,
                subgraph_id="challenger_review",
                confidence=result.confidence,
            ))

            # 复核 → 初审的边（支持或冲突取决于分数差异）
            score_diff = abs(self._junior_score - self._challenger_score)
            relation = "conflict" if score_diff > 20 else "support"
            weight = min(0.95, 0.5 + score_diff / 100)

            self.graph.add_edge(EvidenceEdge(
                source_id="challenger_conclusion",
                target_id="junior_conclusion",
                relation=relation,
                weight=weight,
            ))

    def _run_fact_check(self) -> None:
        """步骤B/C：事实核查 Agent。"""
        draft_report = self._junior_report
        draft_score = self._junior_score

        result = self.fact_check_agent.run(
            self._anomalies, self._stats, draft_report, draft_score
        )
        self.agent_results.append(result)

        if result.status == "success":
            fc = FactCheckResult.from_payload(result.output)

            self.graph.add_node(EvidenceNode(
                node_id="fact_check_result",
                node_type="FactCheckResult",
                content=fc.analysis,
                subgraph_id="fact_check",
                confidence=result.confidence,
            ))

            # 事实核查 → 初审（支持边）
            if fc.support_score > 0.5:
                self.graph.add_edge(EvidenceEdge(
                    source_id="fact_check_result",
                    target_id="junior_conclusion",
                    relation="support",
                    weight=fc.support_score,
                ))

            # 事实核查 → 初审（冲突边）
            if fc.conflict_score > 0.3:
                self.graph.add_edge(EvidenceEdge(
                    source_id="fact_check_result",
                    target_id="junior_conclusion",
                    relation="conflict",
                    weight=fc.conflict_score,
                ))

    def _run_consistency_eval(self) -> None:
        """步骤C/D：一致性评分与状态转移决策。"""
        score = self.graph.calculate_consistency_score()
        conflict_count = self.graph.calculate_conflict_edge_count()
        self.state_machine.transition(score, conflict_count)

    def _run_conflict_resolution(self) -> None:
        """步骤D：冲突消解。"""
        conflict_edges = self.graph.get_conflict_edges()
        junior_node = self.graph.nodes.get("junior_conclusion")
        challenger_node = self.graph.nodes.get("challenger_conclusion")

        resolution = self.fact_check_agent.resolve_conflicts(
            conflict_edges, junior_node, challenger_node
        )

        self.agent_results.append(AgentResult(
            agent_id="conflict_resolution",
            status="success",
            output={"resolution": resolution},
            confidence=0.6,
        ))

    def _run_local_rollback(self) -> None:
        """步骤D：局部回退（权利要求4）。"""
        local_scores = self.graph.calculate_all_local_scores()

        if not local_scores:
            return

        worst_subgraph = min(local_scores, key=local_scores.get)
        self.graph.remove_subgraph(worst_subgraph)
        self.state_machine.set_rollback_target(STATE_JUNIOR_AUDIT)

    def _run_senior_partner(self) -> None:
        """步骤E：高级合伙人最终裁决。"""
        result = self.senior_partner_agent.run(
            total_records=self._stats.get("total_records", 0),
            anomaly_count=self._stats.get("anomaly_count", 0),
            junior_report=self._junior_report,
            junior_score=self._junior_score,
            challenger_rebuttal=self._challenger_rebuttal,
            challenger_score=self._challenger_score,
        )
        self.agent_results.append(result)

        if result.status == "success":
            output = result.output
            verdict = output.get("final_verdict", "False Positive")
            reasoning = output.get("reasoning", "")
            action_item = output.get("action_item", "")

            self.graph.add_node(EvidenceNode(
                node_id="senior_partner_verdict",
                node_type="SeniorPartnerVerdict",
                content=f"[{verdict}] {reasoning}",
                subgraph_id="senior_partner",
                confidence=result.confidence,
            ))

            # 所有结论 → 最终裁决的边
            for conclusion_id in ["junior_conclusion", "challenger_conclusion", "fact_check_result"]:
                if conclusion_id in self.graph.nodes:
                    self.graph.add_edge(EvidenceEdge(
                        source_id=conclusion_id,
                        target_id="senior_partner_verdict",
                        relation="support",
                        weight=0.8,
                    ))

    def _run_workpaper_generation(self) -> None:
        """步骤E：生成工作底稿并恢复隐私映射。"""
        pass  # 底稿在 _build_result 中生成

    def _build_result(self) -> AuditPipelineResult:
        """构造最终结果。"""
        graph_snapshot = self.graph.serialize()
        workpaper_md = self.graph.export_working_paper()
        global_score = self.graph.calculate_consistency_score()
        local_scores = self.graph.calculate_all_local_scores()

        # 恢复隐私映射
        workpaper_md = self.privacy_layer.restore_text(workpaper_md)
        for node in graph_snapshot["nodes"]:
            node["content"] = self.privacy_layer.restore_text(node["content"])

        return AuditPipelineResult(
            global_consistency_score=round(global_score, 4),
            local_subgraph_scores={k: round(v, 4) for k, v in local_scores.items()},
            current_state=self.state_machine.get_current_state(),
            state_history=self.state_machine.get_state_history(),
            agent_results=self.agent_results,
            evidence_graph_snapshot=graph_snapshot,
            workpaper_markdown=workpaper_md,
            rollback_count=self.state_machine.iteration,
            consistency_threshold=self.state_machine.threshold,
            stats=self._stats,
            rule_findings=[
                {"label": f.label, "record_count": f.record_count, "summary": f.summary}
                for f in self._rule_findings
            ],
            privacy_log=self.privacy_layer.get_privacy_log(),
        )
