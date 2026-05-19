# -*- coding: utf-8 -*-
"""
最小证据图实现。

本模块仅负责承载节点、边以及专利中的全局一致性评分公式，
暂不引入额外的图算法或上层业务耦合。
"""

from core.contracts import EvidenceEdge, EvidenceNode


class EvidenceGraph:
    """
    极简证据图结构。
    """

    def __init__(self) -> None:
        # 节点使用字典按 node_id 索引，便于后续快速覆盖或查询。
        self.nodes: dict[str, EvidenceNode] = {}
        # 边按写入顺序保存，便于直接做全局评分计算。
        self.edges: list[EvidenceEdge] = []

    def add_node(self, node: EvidenceNode) -> None:
        """
        添加一个证据节点。
        """
        self.nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceEdge) -> None:
        """
        添加一条证据边。
        """
        self.edges.append(edge)

    def calculate_consistency_score(self) -> float:
        """
        按专利公式计算全局一致性评分。

        公式：
            (支持边权重总和 - 冲突边权重总和) / 总边数

        若当前图中没有边，则返回 1.0 作为默认一致状态。
        """
        if not self.edges:
            return 1.0

        support_sum = 0.0
        conflict_sum = 0.0

        for edge in self.edges:
            relation = edge.relation.strip().lower()

            # 同时兼容英文和中文关系标签，避免上层枚举尚未完全冻结时失效。
            if relation in {"support", "supports", "支持"}:
                support_sum += edge.weight
            elif relation in {"conflict", "conflicts", "冲突"}:
                conflict_sum += edge.weight

        return (support_sum - conflict_sum) / len(self.edges)

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
