# -*- coding: utf-8 -*-
"""
事实核查 Agent 引擎。
对底稿结论进行证据级核验，输出分析文本以及可量化的一致性评分。
支持 BYOK 多模型路由：Ollama / DeepSeek / OpenAI。
"""

from openai import OpenAI


class FactCheckAgent:
    """
    事实核查 Agent。

    输入要求：
        - 需要原始异常数据、统计信息，以及待核查的底稿结论。
        - `api_key` 与 `api_base` 必须能访问兼容 OpenAI 的模型接口。

    输出内容：
        - 返回模型生成的 JSON 字符串。
        - JSON 中必须包含 `analysis`、`support_score`、`conflict_score`。

    可能抛出的异常：
        - `RuntimeError`：API Key 缺失或模型调用失败时抛出。
    """

    def __init__(self, lang: str = "English", api_key: str = "", api_base: str = ""):
        """
        初始化 LLM 客户端，由上层路由配置驱动。

        Args:
            lang: 界面语言，"English" 或 "中文"，控制大模型输出语言。
            api_key: 从上层状态传入的 API Key（云端）或占位符（Ollama）。
            api_base: 从上层状态传入的目标接口地址。

        Returns:
            None。

        Raises:
            RuntimeError: API Key 为空时抛出。
        """
        self.lang = lang
        self.api_key = api_key
        self.api_base = api_base
        self.model = "llama3:8b" if "localhost" in api_base else "gpt-4o-mini"

        print("-" * 40)
        print(f"[FactCheckAgent] 目标接口: {self.api_base}")
        print(f"[FactCheckAgent] 使用模型: {self.model}")
        print("-" * 40)

        if not self.api_key:
            raise RuntimeError("API Key is empty. Please configure it in the sidebar.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    @staticmethod
    def _format_anomalies(anomalies_dict: dict) -> str:
        """
        将异常 DataFrame 字典转换为便于模型阅读的纯文本。

        Args:
            anomalies_dict: 键为异常类型名称，值为异常行 DataFrame。

        Returns:
            格式化后的异常文本；若无异常则返回兜底说明。

        Raises:
            AttributeError: 当传入对象不具备 DataFrame 所需属性时可能抛出。
        """
        lines = []
        for label, df in anomalies_dict.items():
            if df.empty:
                continue
            lines.append(f"## {label} ({len(df)} record(s))")
            lines.append(df.to_string(index=False))
            lines.append("")

        return "\n".join(lines) if lines else "No anomalies found."

    def generate_fact_check(
        self,
        anomalies_dict: dict,
        stats: dict,
        draft_report: str,
        draft_risk_score: int,
    ) -> str:
        """
        发送事实核查请求，返回结构化 JSON 字符串。

        Args:
            anomalies_dict: 异常分类字典。
            stats: 统计指标字典。
            draft_report: 待核查的底稿分析文本。
            draft_risk_score: 底稿当前风险分值，取值通常为 0-100。

        Returns:
            LLM 返回的 JSON 字符串。

        Raises:
            RuntimeError: API 调用失败时抛出。
        """
        anomaly_text = self._format_anomalies(anomalies_dict)
        total_records = stats.get("total_records", "N/A")
        anomaly_count = stats.get("anomaly_count", "N/A")

        system_prompt = (
            "You are FactCheckAgent, a rigorous evidence-verification reviewer. "
            "Your task is to examine raw anomaly evidence against a draft audit conclusion "
            "and determine how strongly the available facts support or conflict with that conclusion. "
            "You MUST respond with a single, valid JSON object ONLY, with no markdown formatting "
            "or surrounding text. The JSON must contain exactly three keys:\n"
            '- "analysis": a concise factual assessment explaining the main evidence alignment and contradictions (string),\n'
            '- "support_score": a floating-point number from 0 to 1 indicating how strongly the evidence supports the draft conclusion,\n'
            '- "conflict_score": a floating-point number from 0 to 1 indicating how strongly the evidence conflicts with the draft conclusion.\n'
            "Both scores are mandatory. Use decimal numbers, not percentages. "
            "Do not omit any key. Example: "
            '{"analysis": "The duplicate payments pattern is supported by repeated vendor-amount pairs, but invoice linkage remains incomplete.", '
            '"support_score": 0.78, "conflict_score": 0.19}'
        )

        if self.lang == "中文":
            system_prompt += (
                "\n\nCRITICAL: You must write the actual text content for your JSON values "
                "entirely in Simplified Chinese (简体中文). Do not change the JSON keys."
            )

        user_prompt = (
            f"Total records scanned: {total_records}\n"
            f"Total anomalies detected: {anomaly_count}\n\n"
            f"=== Raw Anomaly Evidence ===\n{anomaly_text}\n\n"
            f"=== Draft Conclusion To Verify ===\n"
            f"Draft Risk Score: {draft_risk_score}/100\n"
            f"Draft Analysis: {draft_report}\n\n"
            "Please perform factual verification and return the required JSON object."
        )

        print(f"[FactCheckAgent] 正在向模型 '{self.model}' 发送事实核查请求...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            print("[FactCheckAgent] 事实核查结果生成成功！")
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"FactCheckAgent API call failed: {e}")
