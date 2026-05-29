# -*- coding: utf-8 -*-
"""
模型注册表。

集中管理全局默认 LLM 配置和各 Agent 的独立模型覆盖，
对上层 Agent 屏蔽底层提供商差异。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from core.contracts import LLMConfig


# ── 提供商预设模板 ──

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3:8b",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
    },
}


class ModelRegistry:
    """
    模型配置注册表。

    维护一份全局默认 LLMConfig，以及可选的 per-agent 覆盖。
    用法::

        registry = ModelRegistry.from_env()
        config = registry.get_config("junior_agent")
    """

    def __init__(
        self,
        default_config: LLMConfig,
        agent_configs: dict[str, LLMConfig] | None = None,
    ) -> None:
        self.default_config = default_config
        self.agent_configs: dict[str, LLMConfig] = agent_configs or {}

    def get_config(self, agent_id: str) -> LLMConfig:
        """返回指定 Agent 的模型配置，未配置则返回全局默认。"""
        return self.agent_configs.get(agent_id, self.default_config)

    # ── 工厂方法 ──

    @classmethod
    def from_env(cls) -> "ModelRegistry":
        """
        从环境变量构建注册表。

        环境变量约定：
            LLM_PROVIDER        全局提供商（默认 openai）
            LLM_API_KEY         全局 API Key
            LLM_BASE_URL        全局 Base URL（覆盖提供商预设）
            LLM_MODEL           全局模型名（覆盖提供商预设）

            JUNIOR_LLM_PROVIDER / JUNIOR_LLM_API_KEY / JUNIOR_LLM_BASE_URL / JUNIOR_LLM_MODEL
            CHALLENGER_LLM_PROVIDER / ...
            FACTCHECK_LLM_PROVIDER / ...
            SENIOR_LLM_PROVIDER / ...

        向后兼容旧变量名：
            OPENAI_API_KEY   当 LLM_API_KEY 未设置时使用
            OPENAI_BASE_URL  当 LLM_BASE_URL 未设置时使用
        """
        # 全局默认配置
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["openai"])

        api_key = (
            os.getenv("LLM_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
            or os.getenv("ANTHROPIC_API_KEY", "")
        )
        base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or preset["base_url"]
        model = os.getenv("LLM_MODEL") or preset["model"]

        default_config = LLMConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        # Per-agent 覆盖
        agent_ids = ["junior", "challenger", "factcheck", "senior"]
        agent_configs: dict[str, LLMConfig] = {}

        for aid in agent_ids:
            prefix = aid.upper()
            agent_provider = os.getenv(f"{prefix}_LLM_PROVIDER")
            agent_api_key = os.getenv(f"{prefix}_LLM_API_KEY")
            agent_base_url = os.getenv(f"{prefix}_LLM_BASE_URL")
            agent_model = os.getenv(f"{prefix}_LLM_MODEL")

            # 只有至少设置了一个覆盖变量时才创建独立配置
            if any([agent_provider, agent_api_key, agent_base_url, agent_model]):
                ap = (agent_provider or provider).strip().lower()
                ap_preset = PROVIDER_PRESETS.get(ap, preset)

                agent_configs[aid] = LLMConfig(
                    provider=ap,
                    api_key=agent_api_key or api_key,
                    base_url=agent_base_url or ap_preset["base_url"],
                    model=agent_model or ap_preset["model"],
                )

        return cls(default_config=default_config, agent_configs=agent_configs)

    def describe(self) -> dict[str, dict[str, str]]:
        """返回当前配置摘要，用于日志或 API 响应（隐藏 API Key）。"""
        def _summary(cfg: LLMConfig) -> dict[str, str]:
            masked_key = cfg.api_key[:8] + "..." if len(cfg.api_key) > 8 else "***"
            return {
                "provider": cfg.provider,
                "model": cfg.model,
                "base_url": cfg.base_url,
                "api_key": masked_key,
            }

        result: dict[str, dict[str, str]] = {"default": _summary(self.default_config)}
        for aid, cfg in self.agent_configs.items():
            result[aid] = _summary(cfg)
        return result
