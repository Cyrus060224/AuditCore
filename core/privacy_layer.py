# -*- coding: utf-8 -*-
"""
可逆隐私脱敏层（权利要求8）。

对高敏感财务数据进行实体级映射脱敏，
在多 Agent 共享语义空间内保持 Embedding 向量严格一致，
推理完成后通过可逆映射恢复原始信息并生成隐私日志。
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import pandas as pd


class PrivacyLayer:
    """
    实体级可逆脱敏层。

    脱敏策略：
    - 人名/公司名 → 伪名（保持语义一致性）
    - 银行账号/身份证号 → 脱敏标识符
    - 金额列不做脱敏（审计核心数据，但记录日志）

    所有映射通过可逆字典存储，支持最终恢复。
    """

    def __init__(self) -> None:
        self._mapping: dict[str, str] = {}
        self._reverse_mapping: dict[str, str] = {}
        self._privacy_log: list[dict[str, Any]] = []
        self._counter = 0

    def _next_pseudonym(self, prefix: str = "ENTITY") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:04d}"

    def anonymize_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
        """
        对 DataFrame 中的敏感列进行实体级脱敏。

        Returns:
            (脱敏后的DataFrame, 可逆映射字典)
        """
        df = df.copy()
        mapping = {}

        for col in df.columns:
            col_lower = col.strip().lower()
            if col_lower in {"name", "姓名", "人员", "vendor", "供应商", "company", "公司"}:
                unique_values = df[col].dropna().unique()
                for val in unique_values:
                    val_str = str(val)
                    if val_str not in self._mapping:
                        pseudonym = self._next_pseudonym("PERSON")
                        self._mapping[val_str] = pseudonym
                        self._reverse_mapping[pseudonym] = val_str
                        self._privacy_log.append({
                            "type": "entity_name",
                            "column": col,
                            "original": val_str,
                            "pseudonym": pseudonym,
                        })
                    mapping[val_str] = self._mapping[val_str]
                df[col] = df[col].map(lambda v: self._mapping.get(str(v), v) if pd.notna(v) else v)

            elif col_lower in {"account", "账号", "account_number", "bank_account", "身份证", "id_number"}:
                unique_values = df[col].dropna().unique()
                for val in unique_values:
                    val_str = str(val)
                    if val_str not in self._mapping:
                        pseudonym = self._next_pseudonym("ACCT")
                        self._mapping[val_str] = pseudonym
                        self._reverse_mapping[pseudonym] = val_str
                        self._privacy_log.append({
                            "type": "account_number",
                            "column": col,
                            "original": val_str,
                            "pseudonym": pseudonym,
                        })
                    mapping[val_str] = self._mapping[val_str]
                df[col] = df[col].map(lambda v: self._mapping.get(str(v), v) if pd.notna(v) else v)

        return df, mapping

    def anonymize_text(self, text: str) -> str:
        """对文本中已知敏感实体进行替换（用于 LLM prompt）。"""
        result = text
        for original, pseudonym in self._mapping.items():
            result = result.replace(original, pseudonym)
        return result

    def restore_mapping(self, result: dict[str, Any]) -> dict[str, Any]:
        """对最终输出中的脱敏标识符进行逆向恢复。"""
        import json
        result_str = json.dumps(result, ensure_ascii=False)
        for pseudonym, original in self._reverse_mapping.items():
            result_str = result_str.replace(pseudonym, original)
        return json.loads(result_str)

    def restore_text(self, text: str) -> str:
        """对文本中的脱敏标识符进行逆向恢复。"""
        result = text
        for pseudonym, original in self._reverse_mapping.items():
            result = result.replace(pseudonym, original)
        return result

    def get_privacy_log(self) -> list[dict[str, Any]]:
        """返回隐私脱敏日志（权利要求8要求输出隐私保护日志）。"""
        return list(self._privacy_log)

    def get_mapping(self) -> dict[str, str]:
        """返回当前映射字典（供编排器保存，用于最终恢复）。"""
        return dict(self._mapping)
