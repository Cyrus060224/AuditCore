"""
数据加载与基础扫描引擎。
负责读取 Excel 审计数据，并执行基础异常检测规则。
"""

import pandas as pd


class AuditDataLoader:
    """审计数据加载器，封装文件读取和异常扫描逻辑。"""

    @staticmethod
    def load_excel(file_obj) -> pd.DataFrame:
        """
        从文件对象读取 Excel 数据。

        Args:
            file_obj: Streamlit 上传组件返回的文件对象。

        Returns:
            包含原始数据的 DataFrame。

        Raises:
            ValueError: 文件为空或格式不合法。
            Exception: 其他读取异常（如文件损坏）。
        """
        try:
            df = pd.read_excel(file_obj, engine="openpyxl")
        except Exception as e:
            raise Exception(f"Failed to read Excel file: {e}")

        if df.empty:
            raise ValueError("The uploaded file contains no data.")

        return df

    @staticmethod
    def basic_scan(df: pd.DataFrame) -> dict:
        """
        执行基础审计扫描，检测负金额和完全重复行，
        同时计算关键统计指标。

        Args:
            df: 原始审计数据。

        Returns:
            包含两个键的字典：
                - "anomalies": 异常分类字典，键为异常类型名称，值为对应的异常行 DataFrame。
                - "stats": 统计指标字典，包含 total_records、anomaly_count、max_amount。
        """
        anomalies = {}

        # 检测 Amount 列为负数的记录
        if "Amount" in df.columns:
            negative_mask = df["Amount"] < 0
            anomalies["Negative Amounts"] = df[negative_mask].copy()

        # 检测完全重复的行
        duplicate_mask = df.duplicated(keep="first")
        anomalies["Duplicate Rows"] = df[duplicate_mask].copy()

        # 计算统计指标
        anomaly_count = sum(len(a) for a in anomalies.values())
        max_amount = float(df["Amount"].max()) if "Amount" in df.columns else None

        return {
            "anomalies": anomalies,
            "stats": {
                "total_records": len(df),
                "anomaly_count": anomaly_count,
                "max_amount": max_amount,
            },
        }
