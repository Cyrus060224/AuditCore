# -*- coding: utf-8 -*-
"""
高级合伙人 Agent 引擎。
接收初级审计员和反方复核的结论，做最终仲裁裁决，输出结构化 JSON。
支持 BYOK 多模型路由：Ollama / DeepSeek / OpenAI。
"""

from openai import OpenAI


class SeniorPartnerAgent:
    """
    高级合伙人 Agent。
    综合初级审计员（Junior）的发现和反方（Challenger）的质疑，
    做出最终裁决，指定下一步具体行动。
    """

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = ""):
        """
        初始化 LLM 客户端，由 app.py 侧边栏的路由配置驱动。

        Args:
            lang: 界面语言，"English" 或 "中文"，控制大模型输出语言。
            api_key: 从 session_state 传入的 API Key。
            api_base: 从 session_state 传入的目标接口地址。

        Raises:
            RuntimeError: API Key 为空时抛出。
        """
        self.lang = lang
        self.api_key = api_key
        self.api_base = api_base
        self.model = "llama3:8b" if "localhost" in api_base else "gpt-4o-mini"

        print("-" * 40)
        print(f"[Senior Partner] 目标接口: {self.api_base}")
        print(f"[Senior Partner] 使用模型: {self.model}")
        print("-" * 40)

        if not self.api_key:
            raise RuntimeError("API Key is empty. Please configure it in the sidebar.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def generate_verdict(
        self,
        total_records: int,
        anomaly_count: int,
        junior_report: str,
        junior_score: int,
        challenger_rebuttal: str,
        challenger_score: int,
    ) -> str:
        """
        核心逻辑：接收两方报告和风险评分，做出最终仲裁。

        Args:
            total_records: 总记录数。
            anomaly_count: 异常总数。
            junior_report: 初级审计员的分析文本。
            junior_score: 初级审计员风险评分 (0-100)。
            challenger_rebuttal: 反方的复核意见文本。
            challenger_score: 反方调整后的风险评分 (0-100)。

        Returns:
            JSON 字符串，包含 final_verdict、final_risk_score、reasoning、action_item。

        Raises:
            RuntimeError: API 调用失败时抛出。
        """
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
            '- "action_item": a concrete, actionable next step, e.g. "Request original invoices" (string).\n'
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

        print(f"[Senior Partner] 正在向模型 '{self.model}' 发送最终仲裁请求...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            print("[Senior Partner] 最终裁决生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Senior Partner API call failed: {e}")
