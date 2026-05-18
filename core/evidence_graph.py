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
