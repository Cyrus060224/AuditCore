"""
初级审计 Agent 引擎。
调用兼容 OpenAI 标准的大模型 API，对异常数据生成分析报告。
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


class JuniorAuditorAgent:
    """初级审计 Agent，负责将异常数据交由 LLM 生成审计意见。"""

    def __init__(self):
        """
        初始化 LLM 客户端。
        逻辑：优先读取环境变量，如果读取失败，绝对强制回退到本地 Ollama 配置。
        """
        # 强制兜底：即便没有 .env 文件，也绝不连外网
        self.api_key = os.environ.get("OPENAI_API_KEY", "ollama_local")
        self.api_base = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
        self.model = os.environ.get("LLM_MODEL", "llama3:8b")

        print("-" * 40)
        print(f"[Agent 诊断] API Key: {self.api_key}")
        print(f"[Agent 诊断] 目标接口: {self.api_base}")
        print(f"[Agent 诊断] 使用模型: {self.model}")
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

    def generate_report(self, anomalies_dict: dict, stats: dict) -> str:
        """
        业务逻辑：组装 Prompt，向大模型发送请求并接收审计报告。
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

        print(f"[Agent] 正在向本地模型 '{self.model}' 发送请求，请观察风扇转速...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            print("[Agent] 报告生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            # 如果本地 Ollama 没开，会在这里被精准捕获并抛出
            raise RuntimeError(f"LLM API call failed (请确认终端已运行 ollama run llama3:8b): {e}")