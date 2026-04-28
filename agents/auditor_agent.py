"""
初级审计 Agent 引擎。
调用兼容 OpenAI 标准的大模型 API，对异常数据生成分析报告。
"""

import os
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI


class JuniorAuditorAgent:
    """初级审计 Agent，负责将异常数据交由 LLM 生成审计意见。"""

    def __init__(self):
        """
        初始化 LLM 客户端。

        从环境变量读取 OPENAI_API_KEY 和 OPENAI_API_BASE（可选，用于兼容 Groq 等）。
        如果未配置 API Key，仅打印警告，不抛出异常，后续调用会返回模拟结果。
        """
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_base = os.environ.get("OPENAI_API_BASE")

        if not self.api_key:
            print("[WARNING] OPENAI_API_KEY not set. Agent will run in Mock Mode.")
            self.client = None
        else:
            kwargs = {"api_key": self.api_key}
            if self.api_base:
                kwargs["base_url"] = self.api_base
            self.client = OpenAI(**kwargs)

    @staticmethod
    def _format_anomalies(anomalies_dict: dict) -> str:
        """
        将异常数据字典转换为纯文本摘要，供 LLM 理解。

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

    def generate_report(self, anomalies_dict: dict, stats: dict) -> str:
        """
        调用 LLM 生成审计报告。如果 API 不可用则返回模拟文本。

        Args:
            anomalies_dict: 异常分类字典，由 basic_scan 返回的 "anomalies" 键提供。
            stats: 统计指标字典，由 basic_scan 返回的 "stats" 键提供。

        Returns:
            LLM 生成的审计报告文本，或模拟文本。
        """
        anomaly_text = self._format_anomalies(anomalies_dict)
        total_records = stats.get("total_records", "N/A")
        anomaly_count = stats.get("anomaly_count", "N/A")

        system_prompt = (
            "You are a meticulous financial auditor. Your role is to review "
            "anomalies detected in a preliminary rule-based scan of accounting records. "
            "Provide a concise, professional summary of the findings, highlight potential "
            "risks, and recommend next steps for deeper investigation."
        )

        user_prompt = (
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"Anomaly details:\n{anomaly_text}\n\n"
            "Please provide your preliminary audit opinion."
        )

        # 无 API Key 或调用失败时，返回模拟报告
        if self.client is None:
            return self._mock_report(anomaly_count, anomalies_dict)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] LLM API call failed: {e}")
            return self._mock_report(anomaly_count, anomalies_dict)

    @staticmethod
    def _mock_report(anomaly_count: int, anomalies_dict: dict) -> str:
        """
        生成模拟审计报告（占位符，用于无 API Key 时的演示）。

        Args:
            anomaly_count: 异常总数。
            anomalies_dict: 异常分类字典，用于列出具体异常类型。

        Returns:
            带 [Mock Mode] 前缀的模拟审计文本。
        """
        anomaly_types = ", ".join(
            label for label, df in anomalies_dict.items() if not df.empty
        ) or "none"

        return (
            "[Mock Mode] LLM is not configured. This is a simulated audit report.\n\n"
            f"The preliminary scan flagged {anomaly_count} anomaly/anomalies across "
            f"the following categories: {anomaly_types}.\n\n"
            "Recommendation: Assign the Challenger Agent to cross-verify these entries "
            "with original receipts and ledger records. Once the OPENAI_API_KEY is configured, "
            "a real AI-generated analysis will replace this message."
        )
