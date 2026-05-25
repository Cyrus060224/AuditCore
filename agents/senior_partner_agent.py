# -*- coding: utf-8 -*-
"""
高级合伙人 Agent 引擎。
继承 BaseLLMAgent，接收初审和复核结论，做最终仲裁裁决。
"""

from __future__ import annotations

from agents.base_agent import BaseLLMAgent
from core.contracts import AgentResult


class SeniorPartnerAgent(BaseLLMAgent):
    """高级合伙人 Agent，综合两方意见做出最终裁决。"""

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = ""):
        super().__init__(agent_id="senior_partner_agent", lang=lang, api_key=api_key, api_base=api_base)

    def run(
        self,
        total_records: int,
        anomaly_count: int,
        junior_report: str,
        junior_score: int,
        challenger_rebuttal: str,
        challenger_score: int,
    ) -> AgentResult:
        """执行最终仲裁，返回标准化 AgentResult。"""
        system_prompt = (
            "You are a highly experienced Audit Partner. You will receive an anomaly "
            "finding from a Junior Auditor and a rebuttal from a Challenger Auditor. "
            "Your job is to weigh both arguments, make a final executive decision, and "
            "suggest a concrete next step.\n\n"
            "You MUST respond with a single, valid JSON object ONLY, with no markdown "
            "formatting or surrounding text. The JSON must contain exactly four keys:\n"
            '- "final_verdict": must be exactly "True Anomaly" or "False Positive" (string),\n'
            '- "final_risk_score": an integer from 0 to 100 (integer),\n'
            '- "reasoning": your final decision rationale, referencing both sides\' arguments (string),\n'
            '- "action_item": a concrete, actionable next step (string).\n'
            'Example: {"final_verdict": "True Anomaly", "final_risk_score": 75, "reasoning": "...", "action_item": "..."}'
        )

        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys. "
                'For "final_verdict", use exactly "True Anomaly" or "False Positive" — do not translate these two values.'
            )

        user_prompt = (
            f"=== CASE SUMMARY ===\n"
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"=== JUNIOR AUDITOR FINDING ===\n"
            f"Risk Score: {junior_score}/100\n"
            f"Analysis: {junior_report}\n\n"
            f"=== CHALLENGER REVIEW ===\n"
            f"Adjusted Risk Score: {challenger_score}/100\n"
            f"Rebuttal: {challenger_rebuttal}\n\n"
            f"Based on both reports above, deliver your final partner verdict as a JSON object."
        )

        try:
            raw = self._call_llm(system_prompt, user_prompt, temperature=0.3, max_tokens=1024)
            output = self._parse_json_response(raw)
            final_score = output.get("final_risk_score", 50)
            confidence = max(0.5, min(1.0, (100 - abs(final_score - 50)) / 80))
            return self._make_result(
                status="success",
                output=output,
                evidence_node_ids=["senior_partner_verdict"],
                confidence=confidence,
            )
        except Exception as e:
            return self._make_result(status="failed", output={"error": str(e)})

    # 向后兼容旧接口
    def generate_verdict(
        self,
        total_records: int,
        anomaly_count: int,
        junior_report: str,
        junior_score: int,
        challenger_rebuttal: str,
        challenger_score: int,
    ) -> str:
        result = self.run(
            total_records, anomaly_count, junior_report, junior_score,
            challenger_rebuttal, challenger_score
        )
        import json
        return json.dumps(result.output)
