# -*- coding: utf-8 -*-
"""
初级审计 Agent 引擎。
继承 BaseLLMAgent，对异常数据生成审计分析报告。
"""

from __future__ import annotations

from agents.base_agent import BaseLLMAgent
from core.contracts import AgentResult


class JuniorAuditorAgent(BaseLLMAgent):
    """初级审计 Agent，负责将异常数据交由 LLM 生成审计意见。"""

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = ""):
        super().__init__(agent_id="junior_agent", lang=lang, api_key=api_key, api_base=api_base)

    def run(self, anomalies_dict: dict, stats: dict) -> AgentResult:
        """执行初审分析，返回标准化 AgentResult。"""
        anomaly_text = self._format_anomalies(anomalies_dict)
        total_records = stats.get("total_records", "N/A")
        anomaly_count = stats.get("anomaly_count", "N/A")

        system_prompt = (
            "You are a meticulous financial auditor. Your role is to review "
            "anomalies detected in a preliminary rule-based scan of accounting records. "
            "You MUST respond with a single, valid JSON object ONLY, with no markdown "
            "formatting or surrounding text. The JSON must contain exactly two keys:\n"
            '- "analysis": a concise, professional summary of the findings (string),\n'
            '- "risk_score": an integer from 0 to 100, where higher means greater fraud risk.\n'
            "Example: {\"analysis\": \"...\", \"risk_score\": 75}"
        )

        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys."
            )

        user_prompt = (
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"Anomaly details:\n{anomaly_text}\n\n"
            "Please provide your preliminary audit opinion as a valid JSON object."
        )

        try:
            raw = self._call_llm(system_prompt, user_prompt, temperature=0.3, max_tokens=1024)
            output = self._parse_json_response(raw)
            risk_score = output.get("risk_score", 50)
            confidence = max(0.3, min(1.0, (100 - abs(risk_score - 50)) / 100))
            return self._make_result(
                status="success",
                output=output,
                evidence_node_ids=["junior_conclusion"],
                confidence=confidence,
            )
        except Exception as e:
            return self._make_result(status="failed", output={"error": str(e)})

    # 向后兼容旧接口
    def generate_report(self, anomalies_dict: dict, stats: dict) -> str:
        result = self.run(anomalies_dict, stats)
        import json
        return json.dumps(result.output)
