# -*- coding: utf-8 -*-
"""
DAG 状态机（权利要求1步骤E / 权利要求10）。

以有向无环图驱动审计工作流的状态转移，
利用一致性评分作为状态转移和动态回退的核心依据。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.contracts import StateMachineNode, TransitionCondition

# ── 状态常量 ──

STATE_INIT = "STATE_INIT"
STATE_RULE_SCAN = "STATE_RULE_SCAN"
STATE_PRIVACY_ANONYMIZE = "STATE_PRIVACY_ANONYMIZE"
STATE_JUNIOR_AUDIT = "STATE_JUNIOR_AUDIT"
STATE_CHALLENGER_REVIEW = "STATE_CHALLENGER_REVIEW"
STATE_FACT_CHECK = "STATE_FACT_CHECK"
STATE_CONSISTENCY_EVAL = "STATE_CONSISTENCY_EVAL"
STATE_CONFLICT_RESOLUTION = "STATE_CONFLICT_RESOLUTION"
STATE_LOCAL_ROLLBACK = "STATE_LOCAL_ROLLBACK"
STATE_SENIOR_PARTNER = "STATE_SENIOR_PARTNER"
STATE_WORKPAPER_GENERATION = "STATE_WORKPAPER_GENERATION"
STATE_FINAL_VERDICT = "STATE_FINAL_VERDICT"


class DAGStateMachine:
    """
    有向无环状态机，驱动多 Agent 审计流程。

    DAG 以数据结构编码（dict[str, StateMachineNode]），
    对应专利中的"结构化工作流定义文件"。
    """

    def __init__(self, threshold: float = 0.80, max_iterations: int = 3) -> None:
        self.threshold = threshold
        self.max_iterations = max_iterations
        self.current_state: str = STATE_INIT
        self.iteration: int = 0
        self.state_history: list[dict[str, Any]] = []
        self._dag: dict[str, StateMachineNode] = self._build_default_dag()
        self._previous_score: float = 1.0
        self._rollback_target: str = ""

    def _build_default_dag(self) -> dict[str, StateMachineNode]:
        """构建默认 DAG 拓扑。"""
        nodes = {
            STATE_INIT: StateMachineNode(
                node_id="n_init", state_name=STATE_INIT, agent_id="",
            ),
            STATE_RULE_SCAN: StateMachineNode(
                node_id="n_rule", state_name=STATE_RULE_SCAN, agent_id="rule_agent",
                dependencies=["n_init"],
            ),
            STATE_PRIVACY_ANONYMIZE: StateMachineNode(
                node_id="n_privacy", state_name=STATE_PRIVACY_ANONYMIZE, agent_id="privacy_layer",
                dependencies=["n_rule"],
            ),
            STATE_JUNIOR_AUDIT: StateMachineNode(
                node_id="n_junior", state_name=STATE_JUNIOR_AUDIT, agent_id="junior_agent",
                dependencies=["n_privacy"],
                transition_condition=TransitionCondition(max_retries=2),
            ),
            STATE_CHALLENGER_REVIEW: StateMachineNode(
                node_id="n_challenger", state_name=STATE_CHALLENGER_REVIEW, agent_id="challenger_agent",
                dependencies=["n_junior"],
            ),
            STATE_FACT_CHECK: StateMachineNode(
                node_id="n_factcheck", state_name=STATE_FACT_CHECK, agent_id="fact_check_agent",
                dependencies=["n_challenger"],
            ),
            STATE_CONSISTENCY_EVAL: StateMachineNode(
                node_id="n_eval", state_name=STATE_CONSISTENCY_EVAL, agent_id="",
                dependencies=["n_factcheck"],
                transition_condition=TransitionCondition(
                    score_threshold=self.threshold,
                    improvement_required=True,
                    max_retries=self.max_iterations,
                    on_failure_target=STATE_CONFLICT_RESOLUTION,
                ),
            ),
            STATE_CONFLICT_RESOLUTION: StateMachineNode(
                node_id="n_conflict", state_name=STATE_CONFLICT_RESOLUTION, agent_id="fact_check_agent",
                dependencies=["n_eval"],
            ),
            STATE_LOCAL_ROLLBACK: StateMachineNode(
                node_id="n_rollback", state_name=STATE_LOCAL_ROLLBACK, agent_id="",
                dependencies=["n_conflict"],
            ),
            STATE_SENIOR_PARTNER: StateMachineNode(
                node_id="n_partner", state_name=STATE_SENIOR_PARTNER, agent_id="senior_partner_agent",
                dependencies=["n_eval"],
            ),
            STATE_WORKPAPER_GENERATION: StateMachineNode(
                node_id="n_workpaper", state_name=STATE_WORKPAPER_GENERATION, agent_id="",
                dependencies=["n_partner"],
            ),
            STATE_FINAL_VERDICT: StateMachineNode(
                node_id="n_final", state_name=STATE_FINAL_VERDICT, agent_id="",
                dependencies=["n_workpaper"],
            ),
        }
        return nodes

    def get_current_state(self) -> str:
        return self.current_state

    def is_terminal(self) -> bool:
        return self.current_state == STATE_FINAL_VERDICT

    def get_state_history(self) -> list[dict[str, Any]]:
        return list(self.state_history)

    def _record_transition(self, from_state: str, to_state: str, score: float, reason: str) -> None:
        self.state_history.append({
            "from": from_state,
            "to": to_state,
            "score": round(score, 4),
            "iteration": self.iteration,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def transition(self, score: float, conflict_count: int) -> str:
        """
        根据一致性评分和冲突边数决定下一状态（权利要求10）。

        Returns:
            下一状态名称。
        """
        if self.current_state == STATE_INIT:
            self._move_to(STATE_RULE_SCAN, score, "初始化完成，进入规则扫描")
        elif self.current_state == STATE_RULE_SCAN:
            self._move_to(STATE_PRIVACY_ANONYMIZE, score, "规则扫描完成，进入隐私脱敏")
        elif self.current_state == STATE_PRIVACY_ANONYMIZE:
            self._move_to(STATE_JUNIOR_AUDIT, score, "隐私脱敏完成，进入初审")
        elif self.current_state == STATE_JUNIOR_AUDIT:
            self._move_to(STATE_CHALLENGER_REVIEW, score, "初审完成，进入复核")
        elif self.current_state == STATE_CHALLENGER_REVIEW:
            self._move_to(STATE_FACT_CHECK, score, "复核完成，进入事实核查")
        elif self.current_state == STATE_FACT_CHECK:
            self._move_to(STATE_CONSISTENCY_EVAL, score, "事实核查完成，进入一致性评估")
        elif self.current_state == STATE_CONSISTENCY_EVAL:
            self._handle_eval_transition(score, conflict_count)
        elif self.current_state == STATE_CONFLICT_RESOLUTION:
            self._move_to(STATE_LOCAL_ROLLBACK, score, "冲突消解完成，进入局部回退")
        elif self.current_state == STATE_LOCAL_ROLLBACK:
            self._move_to(STATE_JUNIOR_AUDIT, score, "局部回退完成，重新执行受影响Agent")
        elif self.current_state == STATE_SENIOR_PARTNER:
            self._move_to(STATE_WORKPAPER_GENERATION, score, "最终裁决完成，生成工作底稿")
        elif self.current_state == STATE_WORKPAPER_GENERATION:
            self._move_to(STATE_FINAL_VERDICT, score, "工作底稿生成完成，流程结束")

        self._previous_score = score
        return self.current_state

    def _handle_eval_transition(self, score: float, conflict_count: int) -> None:
        """一致性评估节点的核心转移逻辑。"""
        cond = self._dag[STATE_CONSISTENCY_EVAL].transition_condition

        # 评分达标 → 进入高级合伙人
        if score >= cond.score_threshold:
            self._move_to(STATE_SENIOR_PARTNER, score, f"一致性评分 {score:.4f} >= 阈值 {cond.score_threshold}，通过")
            return

        # 超过最大迭代次数 → 强制推进（防止死循环）
        if self.iteration >= cond.max_retries:
            self._move_to(STATE_SENIOR_PARTNER, score, f"已达最大迭代次数 {cond.max_retries}，强制推进")
            return

        # 评分未改善 → 强制推进
        if cond.improvement_required and self.iteration > 0 and score <= self._previous_score:
            self._move_to(STATE_SENIOR_PARTNER, score, f"评分未改善 ({score:.4f} <= {self._previous_score:.4f})，强制推进")
            return

        # 评分不达标 → 冲突消解 → 局部回退
        self.iteration += 1
        self._move_to(STATE_CONFLICT_RESOLUTION, score, f"一致性评分 {score:.4f} < 阈值 {cond.score_threshold}，触发冲突消解")

    def _move_to(self, state: str, score: float, reason: str) -> None:
        self._record_transition(self.current_state, state, score, reason)
        self.current_state = state

    def should_rollback(self) -> bool:
        """当前状态是否需要回退。"""
        return self.current_state == STATE_LOCAL_ROLLBACK

    def get_rollback_target(self) -> str:
        """返回回退目标状态（局部回退，权利要求4）。"""
        if self._rollback_target:
            return self._rollback_target
        return STATE_JUNIOR_AUDIT

    def set_rollback_target(self, target: str) -> None:
        """设置回退目标（由编排器根据最低局部子图评分决定）。"""
        self._rollback_target = target

    def reset_to_state(self, state_name: str) -> None:
        """重置到指定状态（回退用）。"""
        self.current_state = state_name

    def get_priority_queue(self, agent_confidences: dict[str, float]) -> list[tuple[str, float]]:
        """
        返回置信度加权的优先级队列（权利要求5）。
        按 confidence 降序排列。
        """
        return sorted(agent_confidences.items(), key=lambda x: x[1], reverse=True)
