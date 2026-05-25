# -*- coding: utf-8 -*-
"""
专利级证据图实现。

本模块承载节点、边、全局/局部一致性评分公式，
以及支撑 DAG 状态机回退所需的子图操作方法。
"""

from __future__ import annotations

from core.contracts import EvidenceEdge, EvidenceNode

_SUPPORT_RELATIONS = {"support", "supports", "支持"}
_CONFLICT_RELATIONS = {"conflict", "conflicts", "冲突"}


class EvidenceGraph:
    """
    证据图结构，支持全局评分、局部子图评分、冲突边查询及回退操作。
    """

    def __init__(self) -> None:
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: list[EvidenceEdge] = []

    # ── 基础操作 ──

    def add_node(self, node: EvidenceNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceEdge) -> None:
        self.edges.append(edge)

    # ── 评分计算（权利要求1步骤C） ──

    def _score_edges(self, edges: list[EvidenceEdge]) -> float:
        """对给定边集合执行一致性评分公式。"""
        if not edges:
            return 1.0

        support_sum = 0.0
        conflict_sum = 0.0

        for edge in edges:
            relation = edge.relation.strip().lower()
            if relation in _SUPPORT_RELATIONS:
                support_sum += edge.weight
            elif relation in _CONFLICT_RELATIONS:
                conflict_sum += edge.weight

        return (support_sum - conflict_sum) / len(edges)

    def calculate_consistency_score(self) -> float:
        """
        计算全局一致性评分。

        公式：(Σ支持边权重 - Σ冲突边权重) / |E|
        无边时返回 1.0。
        """
        return self._score_edges(self.edges)

    def calculate_local_subgraph_score(self, subgraph_id: str) -> float:
        """
        计算指定局部子图的一致性评分（权利要求1步骤C / 权利要求4）。
        仅统计两端节点均属于该 subgraph_id 的边。
        """
        subgraph_nodes = {
            nid for nid, n in self.nodes.items() if n.subgraph_id == subgraph_id
        }
        if not subgraph_nodes:
            return 1.0

        local_edges = [
            e for e in self.edges
            if e.source_id in subgraph_nodes and e.target_id in subgraph_nodes
        ]
        return self._score_edges(local_edges)

    def calculate_all_local_scores(self) -> dict[str, float]:
        """返回所有子图的局部一致性评分。"""
        return {
            sid: self.calculate_local_subgraph_score(sid)
            for sid in self.get_subgraph_ids()
        }

    # ── 冲突边查询 ──

    def get_conflict_edges(self) -> list[EvidenceEdge]:
        """返回所有冲突关系的边。"""
        return [
            e for e in self.edges
            if e.relation.strip().lower() in _CONFLICT_RELATIONS
        ]

    def get_conflict_edges_for_subgraph(self, subgraph_id: str) -> list[EvidenceEdge]:
        """返回指定子图内的冲突边。"""
        subgraph_nodes = {
            nid for nid, n in self.nodes.items() if n.subgraph_id == subgraph_id
        }
        return [
            e for e in self.edges
            if e.relation.strip().lower() in _CONFLICT_RELATIONS
            and e.source_id in subgraph_nodes
            and e.target_id in subgraph_nodes
        ]

    def calculate_conflict_edge_count(self) -> int:
        """返回冲突边总数，作为收敛指标。"""
        return len(self.get_conflict_edges())

    # ── 子图查询 ──

    def get_subgraph_ids(self) -> list[str]:
        """返回所有不重复的 subgraph_id。"""
        return list({n.subgraph_id for n in self.nodes.values() if n.subgraph_id})

    def get_nodes_by_subgraph(self, subgraph_id: str) -> list[EvidenceNode]:
        """返回属于指定子图的所有节点。"""
        return [n for n in self.nodes.values() if n.subgraph_id == subgraph_id]

    # ── 回退操作（权利要求4） ──

    def remove_node(self, node_id: str) -> None:
        """删除节点及其所有关联边。"""
        self.nodes.pop(node_id, None)
        self.edges = [
            e for e in self.edges
            if e.source_id != node_id and e.target_id != node_id
        ]

    def remove_edges_for_subgraph(self, subgraph_id: str) -> None:
        """删除子图内所有边（局部回退用）。"""
        subgraph_nodes = {
            nid for nid, n in self.nodes.items() if n.subgraph_id == subgraph_id
        }
        self.edges = [
            e for e in self.edges
            if e.source_id not in subgraph_nodes or e.target_id not in subgraph_nodes
        ]

    def remove_subgraph(self, subgraph_id: str) -> None:
        """删除整个子图的节点和边（完整局部回退）。"""
        node_ids = [
            nid for nid, n in self.nodes.items() if n.subgraph_id == subgraph_id
        ]
        for nid in node_ids:
            self.remove_node(nid)

    # ── 序列化 ──

    def serialize(self) -> dict:
        """将图序列化为 JSON 字典。"""
        return {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type,
                    "content": n.content,
                    "subgraph_id": n.subgraph_id,
                    "confidence": n.confidence,
                    "metadata": n.metadata,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
        }

    def export_working_paper(self) -> str:
        """
        基于图谱内冻结结构导出结构化审计工作底稿（Markdown）。
        """
        consistency_score = self.calculate_consistency_score()
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)

        rule_nodes = [node for node in self.nodes.values() if node.node_type == "RuleFinding"]
        junior_node = self.nodes.get("junior_conclusion")
        challenger_node = self.nodes.get("challenger_conclusion")

        relation_lines = []
        for edge in self.edges:
            relation_lines.append(
                f"- {edge.source_id} -> {edge.target_id} | relation: {edge.relation} | weight: {edge.weight:.2f}"
            )

        if not relation_lines:
            relation_lines.append("- 暂无逻辑连线。")

        arbitration_conclusion = "未记录最终仲裁结论。"
        if junior_node and challenger_node:
            for edge in self.edges:
                if edge.source_id == challenger_node.node_id and edge.target_id == junior_node.node_id:
                    edge_relation = edge.relation.strip().lower()
                    if edge_relation in {"support", "supports", "支持"}:
                        arbitration_conclusion = "最终轨迹显示为支持：复核意见对初审结论形成支持。"
                    elif edge_relation in {"conflict", "conflicts", "冲突"}:
                        arbitration_conclusion = "最终轨迹显示为冲突：复核意见与初审结论存在冲突，需经仲裁确认。"
                    else:
                        arbitration_conclusion = f"最终轨迹显示为 {edge.relation}。"
                    break

        lines = [
            "# 审计工作底稿",
            "",
            "## 审计概览",
            f"- 全局一致性评分: {consistency_score:.2f}",
            f"- 总证据节点数: {total_nodes}",
            f"- 总逻辑边数: {total_edges}",
            "",
            "## 基础事实清单",
        ]

        if rule_nodes:
            for node in rule_nodes:
                lines.append(f"- {node.content}")
        else:
            lines.append("- 未发现 RuleFinding 事实节点。")

        lines.extend(
            [
                "",
                "## 图谱博弈与仲裁轨迹",
                "### 初审核心意见",
                f"- {junior_node.content if junior_node else '未记录初审节点。'}",
                "### 复核核心意见",
                f"- {challenger_node.content if challenger_node else '未记录复核节点。'}",
                "### 连线状态",
            ]
        )
        lines.extend(relation_lines)
        lines.extend(
            [
                "### 最终仲裁结论",
                f"- {arbitration_conclusion}",
            ]
        )

        return "\n".join(lines)
