# -*- coding: utf-8 -*-
"""
规则穿透 Agent 引擎。
负责接收结构化表格数据，执行基础硬规则扫描，并输出结构化规则事实。
"""

from __future__ import annotations

import pandas as pd

from core.contracts import RuleFinding


class RuleAgent:
    """
    规则穿透 Agent。

    输入要求：
        - 输入必须为 Pandas DataFrame。
        - 若存在金额字段，字段名应为 `Amount`。

    输出内容：
        - `scan()` 返回 `list[RuleFinding]`。
        - `build_scan_result()` 返回兼容当前 MVP 的扫描结果字典。

    可能抛出的异常：
        - TypeError: 输入不是 DataFrame 时抛出。
    """

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> None:
        """
        校验扫描输入，避免非表格对象进入规则层。

        Args:
            df: 待扫描的表格数据。

        Returns:
            None。

        Raises:
            TypeError: 输入不是 DataFrame 时抛出。
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("RuleAgent expects a pandas DataFrame as input.")

    @staticmethod
    def _collect_anomalies(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        执行基础硬规则扫描，提取异常明细。

        Args:
            df: 原始审计数据。

        Returns:
            以异常标签为键、异常行 DataFrame 为值的字典。

        Raises:
            TypeError: 输入不是 DataFrame 时抛出。
        """
        RuleAgent._validate_dataframe(df)

        anomalies: dict[str, pd.DataFrame] = {}

        # 业务意图：负金额通常对应异常冲销、错误录入或需额外解释的资金流。
        if "Amount" in df.columns:
            negative_mask = df["Amount"] < 0
            anomalies["Negative Amounts"] = df[negative_mask].copy()

        # 业务意图：完全重复行是最小可用版本下的重复报销/重复入账信号。
        duplicate_mask = df.duplicated(keep="first")
        anomalies["Duplicate Rows"] = df[duplicate_mask].copy()

        return anomalies

    @staticmethod
    def _build_stats(df: pd.DataFrame, anomalies: dict[str, pd.DataFrame]) -> dict[str, int | float | None]:
        """
        计算当前规则扫描阶段的统计摘要。

        Args:
            df: 原始审计数据。
            anomalies: 已提取的异常明细字典。

        Returns:
            包含总记录数、异常条数和最大金额的统计字典。

        Raises:
            TypeError: 输入不是 DataFrame 时抛出。
        """
        RuleAgent._validate_dataframe(df)

        anomaly_count = sum(len(anomaly_df) for anomaly_df in anomalies.values())
        max_amount = float(df["Amount"].max()) if "Amount" in df.columns else None

        return {
            "total_records": len(df),
            "anomaly_count": anomaly_count,
            "max_amount": max_amount,
        }

    def scan(self, df: pd.DataFrame) -> list[RuleFinding]:
        """
        执行规则扫描，并将结果封装为 RuleFinding 对象列表。

        Args:
            df: 原始审计数据。

        Returns:
            `list[RuleFinding]`，每个对象对应一类规则发现。

        Raises:
            TypeError: 输入不是 DataFrame 时抛出。
        """
        anomalies = self._collect_anomalies(df)
        return self._build_findings(anomalies)

    @staticmethod
    def _build_findings(anomalies: dict[str, pd.DataFrame]) -> list[RuleFinding]:
        """
        将异常明细聚合为 RuleFinding 列表。

        Args:
            anomalies: 以异常标签为键、异常行 DataFrame 为值的字典。

        Returns:
            `list[RuleFinding]`。

        Raises:
            无。
        """
        findings = []
        for label, anomaly_df in anomalies.items():
            findings.append(
                RuleFinding(
                    label=label,
                    record_count=len(anomaly_df),
                    summary=f"{label}: {len(anomaly_df)} record(s)",
                )
            )

        return findings

    def build_scan_result(self, df: pd.DataFrame) -> dict:
        """
        生成兼容当前 MVP 的完整扫描结果。

        Args:
            df: 原始审计数据。

        Returns:
            包含 `anomalies`、`stats`、`rule_findings` 的字典。

        Raises:
            TypeError: 输入不是 DataFrame 时抛出。
        """
        anomalies = self._collect_anomalies(df)
        stats = self._build_stats(df, anomalies)
        rule_findings = self._build_findings(anomalies)

        return {
            "anomalies": anomalies,
            "stats": stats,
            "rule_findings": rule_findings,
        }
