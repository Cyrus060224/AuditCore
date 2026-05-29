# -*- coding: utf-8 -*-
"""
事实核查 Agent 引擎。
继承 BaseLLMAgent，对底稿结论进行证据级核验。
"""

from __future__ import annotations

from agents.base_agent import BaseLLMAgent
from core.contracts import AgentResult, EvidenceEdge, EvidenceNode, LLMConfig


class FactCheckAgent(BaseLLMAgent):
    """事实核查 Agent，验证证据支撑度并输出一致性评分。"""

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = "", config: LLMConfig | None = None):
        super().__init__(agent_id="fact_check_agent", lang=lang, api_key=api_key, api_base=api_base, config=config)

    def run(
        self,
        anomalies_dict: dict,
        stats: dict,
        draft_report: str,
        draft_risk_score: int,
    ) -> AgentResult:
        """执行事实核查，返回标准化 AgentResult。"""
        anomaly_text = self._format_anomalies(anomalies_dict)
        total_records = stats.get("total_records", "N/A")
        anomaly_count = stats.get("anomaly_count", "N/A")

        system_prompt = (
            "You are FactCheckAgent, a rigorous evidence-verification reviewer. "
            "Your task is to examine raw anomaly evidence against a draft audit conclusion "
            "and determine how strongly the available facts support or conflict with that conclusion. "
            "You MUST respond with a single, valid JSON object ONLY, with no markdown formatting "
            "or surrounding text. The JSON must contain exactly three keys:\n"
            '- "analysis": a concise factual assessment (string),\n'
            '- "support_score": a float from 0 to 1 indicating evidence support strength,\n'
            '- "conflict_score": a float from 0 to 1 indicating evidence conflict strength.\n'
            "Both scores are mandatory. Use decimal numbers, not percentages. "
            "Example: "
            '{"analysis": "...", "support_score": 0.78, "conflict_score": 0.19}'
        )

        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys."
            )

        user_prompt = (
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"=== Raw Anomaly Evidence ===\n{anomaly_text}\n\n"
            f"=== Draft Conclusion To Verify ===\n"
            f"Draft Risk Score: {draft_risk_score}/100\n"
            f"Draft Analysis: {draft_report}\n\n"
            "Please perform factual verification and return the required JSON object."
        )

        try:
            raw = self._call_llm(system_prompt, user_prompt, temperature=0.4, max_tokens=1024)
            output = self._parse_json_response(raw)
            support_score = float(output.get("support_score", 0.5))
            confidence = max(0.3, min(1.0, support_score))
            return self._make_result(
                status="success",
                output=output,
                evidence_node_ids=["fact_check_result"],
                confidence=confidence,
            )
        except Exception as e:
            return self._make_result(status="failed", output={"error": str(e)})

    def resolve_conflicts(
        self,
        conflict_edges: list[EvidenceEdge],
        junior_node: EvidenceNode | None,
        challenger_node: EvidenceNode | None,
    ) -> str:
        """对冲突边进行深度仲裁，返回仲裁结论文本。"""
        edge_lines = []
        for edge in conflict_edges:
            edge_lines.append(
                f"- source={edge.source_id}, target={edge.target_id}, "
                f"relation={edge.relation}, weight={edge.weight:.2f}"
            )
        conflict_text = "\n".join(edge_lines) if edge_lines else "No explicit conflict edges were provided."

        junior_text = junior_node.content if junior_node else "Junior conclusion node is missing."
        challenger_text = challenger_node.content if challenger_node else "Challenger conclusion node is missing."

        system_prompt = (
            "You are a senior audit manager performing final arbitration in a multi-agent audit workflow. "
            "Your job is to resolve conflicts between a junior auditor's initial conclusion and a challenger "
            "reviewer's rebuttal using the provided evidence graph conflict edges. "
            "Return a clear arbitration conclusion in plain text. Include: final judgment, key reason, "
            "which side is better supported, and the next audit action. Do not use markdown tables."
        )

        if self.lang == "中文":
            system_prompt += "\n\n请使用简体中文输出仲裁结论。"

        user_prompt = (
            "=== Junior Auditor Conclusion ===\n"
            f"{junior_text}\n\n"
            "=== Challenger Review Conclusion ===\n"
            f"{challenger_text}\n\n"
            "=== Evidence Graph Conflict Edges ===\n"
            f"{conflict_text}\n\n"
            "As the senior audit manager, arbitrate this conflict and provide the final conflict-resolution conclusion."
        )

        try:
            return self._call_llm(system_prompt, user_prompt, temperature=0.2, max_tokens=1200, json_mode=False)
        except Exception as e:
            return f"Conflict resolution failed: {e}"

    # 向后兼容旧接口
    def generate_fact_check(
        self, anomalies_dict: dict, stats: dict, draft_report: str, draft_risk_score: int
    ) -> str:
        result = self.run(anomalies_dict, stats, draft_report, draft_risk_score)
        import json
        return json.dumps(result.output)
