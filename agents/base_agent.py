# -*- coding: utf-8 -*-
"""
LLM Agent 共享基类。

封装 OpenAI 客户端初始化、异常数据格式化、JSON 解析等公共逻辑，
消除各 Agent 文件中的重复代码。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from openai import OpenAI

from core.contracts import AgentResult


class BaseLLMAgent(ABC):
    """
    所有 LLM Agent 的抽象基类。

    子类只需实现 run() 方法，返回标准 AgentResult。
    """

    def __init__(self, agent_id: str, lang: str, api_key: str, api_base: str) -> None:
        self.agent_id = agent_id
        self.lang = lang
        self.api_key = api_key
        self.api_base = api_base
        self.model = "llama3:8b" if "localhost" in api_base else "gpt-4o-mini"

        if not self.api_key:
            raise RuntimeError("API Key is empty. Please configure it in the sidebar.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    # ── 共享工具方法 ──

    @staticmethod
    def _format_anomalies(anomalies_dict: dict) -> str:
        """将异常 DataFrame 字典转换为 LLM 可读的纯文本。"""
        lines = []
        for label, df in anomalies_dict.items():
            if df.empty:
                continue
            lines.append(f"## {label} ({len(df)} record(s))")
            lines.append(df.to_string(index=False))
            lines.append("")
        return "\n".join(lines) if lines else "No anomalies found."

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        json_mode: bool = True,
    ) -> str:
        """统一的 LLM 调用封装。"""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        """安全解析 LLM 返回的 JSON 字符串。"""
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    def _make_result(
        self,
        status: str,
        output: dict,
        evidence_node_ids: list[str] | None = None,
        confidence: float = 1.0,
    ) -> AgentResult:
        """构造标准 AgentResult。"""
        return AgentResult(
            agent_id=self.agent_id,
            status=status,
            output=output,
            evidence_node_ids=evidence_node_ids or [],
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ── 子类必须实现 ──

    @abstractmethod
    def run(self, *args, **kwargs) -> AgentResult:
        """执行 Agent 核心逻辑，返回标准化结果。"""
        ...
