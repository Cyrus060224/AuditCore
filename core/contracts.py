# -*- coding: utf-8 -*-
"""
专利原生中间数据契约。

本模块先冻结多 Agent 审计流程中的关键结构，
为后续证据图、一致性评分函数、DAG 状态机提供稳定输入输出边界。
"""

from dataclasses import dataclass, field
from enum import Enum
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


# ── 冲突类型枚举（权利要求6） ──


class ConflictType(str, Enum):
    """证据冲突分类，对应权利要求6中的三种冲突形式。"""

    NUMERICAL = "numerical"   # 数值冲突：金额/比率不一致
    LOGICAL = "logical"       # 逻辑冲突：结论互斥
    TEMPORAL = "temporal"     # 时间冲突：时序矛盾


# ── Agent 统一输出契约 ──


@dataclass
class AgentResult:
    """
    各 Agent 的标准化输出包装器。

    所有 Agent（规则穿透、初审、复核、事实核查、高级合伙人）
    均通过此结构向编排器返回结果，消除对原始 JSON 字符串的直接依赖。
    """

    agent_id: str
    status: str  # "success" | "failed" | "skipped"
    output: dict[str, Any] = field(default_factory=dict)
    evidence_node_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: str = ""


# ── DAG 状态机契约 ──


@dataclass
class TransitionCondition:
    """
    状态转移条件（权利要求10）。

    当一致性评分满足阈值要求或改善幅度达标时，状态机放行至下一节点。
    """

    score_threshold: float = 0.80
    improvement_required: bool = False
    max_retries: int = 3
    on_failure_target: str = ""


@dataclass
class StateMachineNode:
    """
    DAG 状态机节点定义。

    对应专利中的"结构化工作流定义文件"，
    描述节点类型、状态转移条件及任务依赖关系。
    """

    node_id: str
    state_name: str
    agent_id: str
    dependencies: list[str] = field(default_factory=list)
    transition_condition: TransitionCondition = field(default_factory=TransitionCondition)


# ── 流水线顶层结果 ──


@dataclass
class AuditPipelineResult:
    """
    编排器 run_pipeline() 的完整返回结构。

    包含全局/局部一致性评分、状态历史、各 Agent 输出、
    证据图快照及最终工作底稿。
    """

    global_consistency_score: float = 1.0
    local_subgraph_scores: dict[str, float] = field(default_factory=dict)
    current_state: str = "STATE_INIT"
    state_history: list[dict[str, Any]] = field(default_factory=list)
    agent_results: list[AgentResult] = field(default_factory=list)
    evidence_graph_snapshot: dict[str, Any] = field(default_factory=dict)
    workpaper_markdown: str = ""
    rollback_count: int = 0
    consistency_threshold: float = 0.80
    stats: dict[str, Any] = field(default_factory=dict)
    rule_findings: list[dict[str, Any]] = field(default_factory=list)
    privacy_log: list[dict[str, Any]] = field(default_factory=list)


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
    subgraph_id: str = ""
    confidence: float = 1.0


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
