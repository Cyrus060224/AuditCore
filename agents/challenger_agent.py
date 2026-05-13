# -*- coding: utf-8 -*-
"""
反方（Challenger）审计 Agent 引擎。
对 Junior 的结论进行复核与质疑，输出独立的审计意见。
支持 BYOK 多模型路由：Ollama / DeepSeek / OpenAI。
"""

from openai import OpenAI


class ChallengerAgent:
    """
    反方审计 Agent。
    不依赖 Junior 的判断逻辑，而是独立评估异常数据后给出反驳意见。
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
        print(f"[Challenger] 目标接口: {self.api_base}")
        print(f"[Challenger] 使用模型: {self.model}")
        print("-" * 40)

        if not self.api_key:
            raise RuntimeError("API Key is empty. Please configure it in the sidebar.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    @staticmethod
    def _format_anomalies(anomalies_dict: dict) -> str:
        """
        数据流转：将 Pandas 抓出的异常 DataFrame 字典，
        转换为纯文本格式，供大模型理解。

        Args:
            anomalies_dict: 键为异常类型名称，值为异常行 DataFrame。

        Returns:
            格式化后的文本摘要。
        """
        lines = []
        for label, df in anomalies_dict.items():
            if df.empty:
                continue
            lines.append(f"## {label} ({len(df)} record(s))")
            lines.append(df.to_string(index=False))
            lines.append("")

        return "\n".join(lines) if lines else "No anomalies found."

    def generate_rebuttal(
        self,
        anomalies_dict: dict,
        stats: dict,
        junior_report: str,
        junior_score: int,
    ) -> str:
        """
        核心逻辑：接收异常数据和 Junior 的报告，
        独立评估后生成反驳意见，返回 JSON 字符串。

        Args:
            anomalies_dict: 异常分类字典。
            stats: 统计指标字典。
            junior_report: Junior Auditor 的分析文本。
            junior_score: Junior 给出的风险评分。

        Returns:
            LLM 返回的 JSON 字符串，包含 rebuttal 和 adjusted_risk_score。

        Raises:
            RuntimeError: API 调用失败时抛出。
        """
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

        print(f"[Challenger] 正在向模型 '{self.model}' 发送复核请求...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            print("[Challenger] 复核意见生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Challenger Agent API call failed: {e}")
