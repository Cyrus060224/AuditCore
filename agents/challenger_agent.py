# -*- coding: utf-8 -*-
"""
反方（Challenger）审计 Agent 引擎。
继承 BaseLLMAgent，对 Junior 的结论进行复核与质疑。
"""

from __future__ import annotations

from agents.base_agent import BaseLLMAgent
from core.contracts import AgentResult, LLMConfig


class ChallengerAgent(BaseLLMAgent):
    """反方审计 Agent，独立评估异常数据后给出反驳意见。"""

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = "", config: LLMConfig | None = None):
        super().__init__(agent_id="challenger_agent", lang=lang, api_key=api_key, api_base=api_base, config=config)

    def run(
        self,
        anomalies_dict: dict,
        stats: dict,
        junior_report: str,
        junior_score: int,
    ) -> AgentResult:
        """执行复核分析，返回标准化 AgentResult。"""
        anomaly_text = self._format_anomalies(anomalies_dict)
        total_records = stats.get("total_records", "N/A")
        anomaly_count = stats.get("anomaly_count", "N/A")

        system_prompt = (
            "You are the Challenger Auditor — a skeptical, independent reviewer tasked "
            "with reviewing the findings of a Junior Auditor. You must examine the raw "
            "anomaly data and decide whether the Junior's conclusion is accurate, "
            "overstated, or understated. You MUST respond with a single, valid JSON object "
            "ONLY, with no markdown formatting or surrounding text. The JSON must contain "
            "exactly two keys:\n"
            '- "rebuttal": your independent analysis (string),\n'
            '- "adjusted_risk_score": your own risk score from 0 to 100 (integer).\n'
            "Example: {\"rebuttal\": \"...\", \"adjusted_risk_score\": 30}"
        )

        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys."
            )

        user_prompt = (
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"=== Raw Anomaly Data ===\n{anomaly_text}\n\n"
            f"=== Junior Auditor's Finding ===\n"
            f"Risk Score: {junior_score}/100\n"
            f"Analysis: {junior_report}\n\n"
            "Please provide your independent rebuttal as a valid JSON object."
        )

        try:
            raw = self._call_llm(system_prompt, user_prompt, temperature=0.4, max_tokens=1024)
            output = self._parse_json_response(raw)
            adjusted_score = output.get("adjusted_risk_score", 50)
            confidence = max(0.3, min(1.0, (100 - abs(adjusted_score - 50)) / 100))
            return self._make_result(
                status="success",
                output=output,
                evidence_node_ids=["challenger_conclusion"],
                confidence=confidence,
            )
        except Exception as e:
            return self._make_result(status="failed", output={"error": str(e)})

    # 向后兼容旧接口
    def generate_rebuttal(
        self, anomalies_dict: dict, stats: dict, junior_report: str, junior_score: int
    ) -> str:
        result = self.run(anomalies_dict, stats, junior_report, junior_score)
        import json
        return json.dumps(result.output)
