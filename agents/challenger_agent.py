# -*- coding: utf-8 -*-
"""
反方审计 Agent 引擎。
复用本地 Llama3:8b 模型，以反方视角对初级审计结果进行复核，降低误报率。
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # 显式指定 .env 路径，基于项目根目录，避免工作目录不确定导致加载失败
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path, override=True)
except ImportError:
    pass

from openai import OpenAI


class ChallengerAgent:
    """
    反方审计 Agent。
    扮演怀疑态度的高级审计合伙人，对初级审计员发现的异常数据
    提出良性解释，旨在降低误报率。
    """

    def __init__(self, lang: str = "English"):
        """
        初始化 LLM 客户端。
        逻辑：优先读取环境变量，如果读取失败，绝对强制回退到本地 Ollama 配置。
        
        Args:
            lang: 界面语言，"English" 或 "中文"。用于控制大模型输出语言。
        """
        self.lang = lang
        # 强制兜底：即便没有 .env 文件，也绝不连外网
        self.api_key = os.environ.get("OPENAI_API_KEY", "ollama_local")
        self.api_base = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
        self.model = os.environ.get("LLM_MODEL", "llama3:8b")

        print("-" * 40)
        print(f"[Challenger Agent 诊断] API Key: {self.api_key}")
        print(f"[Challenger Agent 诊断] 目标接口: {self.api_base}")
        print(f"[Challenger Agent 诊断] 使用模型: {self.model}")
        print("-" * 40)

        # 实例化客户端，严格锁死目标地址
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )

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

    def generate_review(self, total_records: int, anomaly_text: str, junior_report: str) -> str:
        """
        核心逻辑：接收总记录数、异常数据文本、初级审计员报告，
        生成反方复核意见。
        """
        system_prompt = (
            "You are a skeptical Senior Audit Partner. Your job is to review the anomalies "
            "found by the Junior Auditor. You must actively look for benign, normal business "
            "explanations for these anomalies (e.g., negative amounts could be refunds or "
            "voided transactions). Your goal is to reduce false positives.\n"
            "You MUST respond with a single, valid JSON object ONLY, with no markdown "
            "formatting or surrounding text. The JSON must contain exactly two keys:\n"
            '- "rebuttal": your independent review and potential false positive analysis (string),\n'
            '- "adjusted_risk_score": an integer from 0 to 100, the adjusted risk score after your review.\n'
            "Example: {\"rebuttal\": \"...\", \"adjusted_risk_score\": 30}"
        )

        # 跨平台语言控制：中文模式下强制模型输出简体中文内容
        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys."
            )

        user_prompt = (
            f"Total records scanned: {total_records}\n\n"
            f"Anomaly data:\n{anomaly_text}\n\n"
            f"Junior Auditor's preliminary report:\n{junior_report}\n\n"
            "Based on the above, provide your independent review. Point out any potential "
            "false positives and offer reasonable business explanations. Keep it concise "
            "and professional."
        )

        print(f"[Challenger Agent] 正在向本地模型 '{self.model}' 发送复核请求...")

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
            print("[Challenger Agent] 复核报告生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(
                f"Challenger Agent API call failed (确认终端已运行 ollama run llama3:8b): {e}"
            )
