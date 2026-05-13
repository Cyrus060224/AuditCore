# -*- coding: utf-8 -*-
"""
初级审计 Agent 引擎。
调用兼容 OpenAI 标准的大模型 API，对异常数据生成分析报告。
支持 BYOK 多模型路由：Ollama / DeepSeek / OpenAI。
"""

from openai import OpenAI


class JuniorAuditorAgent:
    """初级审计 Agent，负责将异常数据交由 LLM 生成审计意见。"""

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = ""):
        """
        初始化 LLM 客户端，由 app.py 侧边栏的路由配置驱动。

        Args:
            lang: 界面语言，"English" 或 "中文"，控制大模型输出语言。
            api_key: 从 session_state 传入的 API Key（云端）或占位符（Ollama）。
            api_base: 从 session_state 传入的目标接口地址。

        Raises:
            RuntimeError: API Key 为空时抛出。
        """
        self.lang = lang
        self.api_key = api_key
        self.api_base = api_base
        self.model = "llama3:8b" if "localhost" in api_base else "gpt-4o-mini"

        print("-" * 40)
        print(f"[Junior Agent] 目标接口: {self.api_base}")
        print(f"[Junior Agent] 使用模型: {self.model}")
        print("-" * 40)

        if not self.api_key:
            raise RuntimeError("API Key is empty. Please configure it in the sidebar.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    @staticmethod
    def _format_anomalies(anomalies_dict: dict) -> str:
        """
        数据流转逻辑：将 Pandas 抓出的异常 DataFrame 字典，
        降维转换成简单的纯文本格式，方便丢给大模型阅读。
        """
        lines = []
        for label, df in anomalies_dict.items():
            if df.empty:
                continue
            lines.append(f"## {label} ({len(df)} record(s))")
            lines.append(df.to_string(index=False))
            lines.append("")

        return "\n".join(lines) if lines else "No anomalies found."

    def generate_report(self, anomalies_dict: dict, stats: dict) -> str:
        """
        业务逻辑：组装 Prompt，向大模型发送请求并接收审计报告。

        Args:
            anomalies_dict: 异常分类字典。
            stats: 统计指标字典。

        Returns:
            LLM 返回的 JSON 字符串。

        Raises:
            RuntimeError: API 调用失败时抛出。
        """
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

        print(f"[Junior Agent] 正在向模型 '{self.model}' 发送请求...")

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
            print("[Junior Agent] 报告生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Junior Agent API call failed: {e}")
