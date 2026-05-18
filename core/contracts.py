# -*- coding: utf-8 -*-
"""
专利原生中间数据契约。

本模块先冻结多 Agent 审计流程中的关键结构，
为后续证据图、一致性评分函数、DAG 状态机提供稳定输入输出边界。
"""

from dataclasses import dataclass, field
from typing import Any


def _clamp_unit_score(value: Any, default: float) -> float:
    """
    将输入值收敛到 0-1 区间，避免上游 JSON 漂移直接污染状态层。

    Args:
        value: 任意待转换值。
        default: 转换失败时的兜底分数。

    Returns:
        0-1 区间内的浮点数。

    Raises:
        ValueError: 当 default 不是合法数值时可能抛出。
    """
    fallback = float(default)

    try:
        score = float(value)
    except (TypeError, ValueError):
        score = fallback

    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


@dataclass
class RuleFinding:
    """
    规则扫描结果契约。

    输入要求：
        - `label` 用于标记规则类别。
        - `record_count` 必须为非负整数。

    输出内容：
        - 结构化规则事实摘要。

    可能抛出的异常：
        - 无主动抛出；由上层负责校验源数据完整性。
    """

    label: str
    record_count: int
    summary: str


@dataclass
class FactCheckResult:
    """
    事实核查结果契约。

    输入要求：
        - 模型输出中应包含 `analysis`、`support_score`、`conflict_score`。

    输出内容：
        - 标准化后的事实核查结果。
        - 可兼容映射为旧版复核文本与风险分。

    可能抛出的异常：
        - 无主动抛出；非法分数会被收敛到安全区间。
    """

    analysis: str
    support_score: float
    conflict_score: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None, fallback_analysis: str = "") -> "FactCheckResult":
        """
        从模型 JSON 解析结果构造标准化事实核查对象。

        Args:
            payload: 解析后的 JSON 字典。
            fallback_analysis: 当 JSON 不完整时使用的兜底文本。

        Returns:
            标准化后的 `FactCheckResult` 实例。

        Raises:
            AttributeError: 当 payload 不是映射对象时可能抛出。
        """
        payload = payload or {}

        analysis = str(payload.get("analysis", fallback_analysis or "No analysis provided."))
        support_score = _clamp_unit_score(payload.get("support_score", 0.5), default=0.5)
        conflict_score = _clamp_unit_score(payload.get("conflict_score", 0.5), default=0.5)

        return cls(
            analysis=analysis,
            support_score=support_score,
            conflict_score=conflict_score,
        )

    def to_legacy_challenger_score(self) -> int:
        """
        将专利阶段的 0-1 支持度临时映射为旧版 0-100 分值。

        Args:
            无。

        Returns:
            0-100 的整数分值。

        Raises:
            无。
        """
        return int(round(self.support_score * 100))


@dataclass
class EvidenceNode:
    """
    审计证据图节点契约。

    输入要求：
        - `node_id` 在一次流程内应唯一。
        - `node_type` 标记节点来源或语义类型。

    输出内容：
        - 图节点基础结构。

    可能抛出的异常：
        - 无主动抛出；唯一性由图构建层保证。
    """

    node_id: str
    node_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceEdge:
    """
    审计证据图边契约。

    输入要求：
        - `relation` 应为支持或冲突语义。
        - `weight` 建议落在 0-1 区间。

    输出内容：
        - 图边基础结构。

    可能抛出的异常：
        - 无主动抛出；权重清洗由上层控制。
    """

    source_id: str
    target_id: str
    relation: str
    weight: float


@dataclass
class DraftWorkpaper:
    """
    结构化审计工作底稿契约。

    输入要求：
        - 包含结论、依据、下一步动作等核心字段。

    输出内容：
        - 后续 DraftAgent 的标准底稿对象。

    可能抛出的异常：
        - 无主动抛出；字段完备性由生成阶段保证。
    """

    conclusion: str
    reasoning: str
    action_item: str
    supporting_node_ids: list[str] = field(default_factory=list)
    conflicting_node_ids: list[str] = field(default_factory=list)
