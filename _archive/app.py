# -*- coding: utf-8 -*-
"""
Streamlit 主入口（MVP 版本）。
侧边栏展示系统环境信息，主界面接收审计文件上传、数据预览及异常扫描。
"""

import json
from dataclasses import asdict
import platform
import streamlit as st
from agents import FactCheckAgent
from agents.rule_agent import RuleAgent
from core.utils import get_project_root, get_mock_data_path
from core.contracts import EvidenceEdge, EvidenceNode, FactCheckResult, RuleFinding
from core.data_loader import AuditDataLoader
from core.evidence_graph import EvidenceGraph
from agents.auditor_agent import JuniorAuditorAgent
from agents.senior_partner_agent import SeniorPartnerAgent

st.set_page_config(page_title="AuditCore", layout="wide", initial_sidebar_state="expanded")
st.markdown('''
<style>
/* 隐藏原生菜单和页脚 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 极简灰白背景与现代无衬线字体 */
.stApp {
    background-color: #fbfbfb;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Metric 核心指标大字号与极客风 */
div[data-testid="stMetricValue"] {
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    letter-spacing: -0.05em;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    text-transform: uppercase;
}

/* 标签页 Tabs 现代化 */
.stTabs [data-baseweb="tab-list"] {
    gap: 30px;
    border-bottom: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    background-color: transparent;
    color: #64748b;
    font-weight: 600;
    border: none;
}
.stTabs [aria-selected="true"] {
    color: #0f172a;
    border-bottom: 2px solid #0f172a !important;
}
</style>
''', unsafe_allow_html=True)

# 跨平台编码声明：文件顶部 # -*- coding: utf-8 -*- 确保 Windows/GBk 环境下不乱码
# 所有字符串操作均基于 Unicode，避免不同操作系统默认编码差异

# i18n 文本字典：根据语言选择动态渲染界面文本
TEXT = {
    "English": {
        "title": "AuditCore - Multi-Agent Audit System MVP",
        "sys_env": "System Environment",
        "cross_platform": "Cross-platform path handler active",
        "uploader_label": "Upload audit file (.xlsx)",
        "data_preview": "Data Preview",
        "total_rows": "Total rows",
        "preliminary_scan": "Preliminary Scan",
        "run_scan": "Run Preliminary Scan",
        "total_records": "Total Records",
        "anomalies_detected": "Anomalies Detected",
        "max_amount": "Max Amount",
        "no_anomalies": "No anomalies found in preliminary scan.",
        "ai_opinion": "AI Agent's Preliminary Opinion",
        "generate_report": "Generate AI Report",
        "junior_finding": "Junior Auditor's Finding",
        "challenger_review": "Challenger's Review",
        "junior_risk": "Junior Risk Score",
        "challenger_risk": "Challenger Risk Score",
        "challenger_not_available": "Challenger report not available.",
        "high_risk": "HIGH RISK: Immediate manual intervention recommended.",
        "low_risk": "LOW RISK: Likely normal business write-offs.",
        "lang_label": "Language / 语言",
        "anomaly_view": "View Anomaly Details",
        "anomaly_detected": "record(s) detected",
        "file_loaded": "File loaded",
        "rows": "rows",
        "failed_process": "Failed to process file",
        "partner_verdict": "Final Partner Verdict",
        "partner_risk": "Partner Risk Score",
        "partner_reasoning": "Final Reasoning",
        "partner_action": "Action Item",
        "partner_not_available": "Partner verdict not available.",
        "action_prefix": "Action: ",
    },
    "中文": {
        "title": "AuditCore 智能审计系统 MVP",
        "sys_env": "系统环境",
        "cross_platform": "跨平台路径处理已激活",
        "uploader_label": "上传审计文件 (.xlsx)",
        "data_preview": "数据预览",
        "total_rows": "总行数",
        "preliminary_scan": "初步扫描",
        "run_scan": "运行初步扫描",
        "total_records": "总记录数",
        "anomalies_detected": "异常检测数",
        "max_amount": "最大金额",
        "no_anomalies": "初步扫描未发现异常。",
        "ai_opinion": "AI Agent 审计意见",
        "generate_report": "生成 AI 报告",
        "junior_finding": "初级审计员结论",
        "challenger_review": "反方复核意见",
        "junior_risk": "初级审计员判定风险",
        "challenger_risk": "反方调整后风险",
        "challenger_not_available": "反方报告不可用。",
        "high_risk": "高风险：建议人工立即介入",
        "low_risk": "低风险：大概率为正常业务冲销",
        "lang_label": "Language / 语言",
        "anomaly_view": "查看异常详情",
        "anomaly_detected": "条记录已检测",
        "file_loaded": "文件已加载",
        "rows": "行",
        "failed_process": "文件处理失败",
        "partner_verdict": "最终合伙人裁决",
        "partner_risk": "合伙人风险评分",
        "partner_reasoning": "最终裁决理由",
        "partner_action": "下一步行动",
        "partner_not_available": "合伙人裁决不可用。",
        "action_prefix": "行动建议: ",
    },
}


VERDICT_MAP = {
    "English": {
        "True Anomaly": "True Anomaly",
        "False Positive": "False Positive",
    },
    "中文": {
        "True Anomaly": "真实异常 (True Anomaly)",
        "False Positive": "误报 (False Positive)",
    },
}

STATE_INIT = "STATE_INIT"
STATE_FINAL_VERDICT = "STATE_FINAL_VERDICT"
STATE_ROLLBACK_REVIEW = "STATE_ROLLBACK_REVIEW"


def ensure_current_evidence_graph(graph) -> EvidenceGraph:
    """
    Streamlit 热重载后，session_state 可能保留旧版 EvidenceGraph 实例。
    这里将旧实例迁移到当前类定义，保留已冻结的 nodes/edges。
    """
    if isinstance(graph, EvidenceGraph) and hasattr(graph, "export_working_paper"):
        return graph

    upgraded_graph = EvidenceGraph()
    upgraded_graph.nodes = getattr(graph, "nodes", {})
    upgraded_graph.edges = getattr(graph, "edges", [])
    return upgraded_graph


def clear_ai_state():
    """
    语言切换时的防御性回调。
    语言改变意味着大模型输出的语言不再匹配当前 UI，
    所有 AI 生成的报告必须清空，强制用户在切换后的语言下重新点击按钮。
    """
    st.session_state.pop("junior_analysis", None)
    st.session_state.pop("junior_score", None)
    st.session_state.pop("challenger_rebuttal", None)
    st.session_state.pop("challenger_score", None)
    st.session_state.pop("fact_check_analysis", None)
    st.session_state.pop("fact_check_support_score", None)
    st.session_state.pop("fact_check_conflict_score", None)
    st.session_state.pop("evidence_graph", None)
    st.session_state.pop("conflict_arbitration", None)
    st.session_state.pop("manual_final_confirmation", None)
    st.session_state.pop("patent_contracts", None)
    st.session_state.pop("partner_verdict", None)
    st.session_state.pop("partner_risk", None)
    st.session_state.pop("partner_reasoning", None)
    st.session_state.pop("partner_action", None)


def reset_all_state():
    """
    清除所有业务缓存状态。
    当用户重新选择文件或点击叉号取消上传时，
    通过 on_change 钩子强制打破 Streamlit 的文件缓存机制，
    确保旧数据不会污染新会话。
    """
    st.session_state.pop("df", None)
    st.session_state.pop("scan_results", None)
    st.session_state.pop("ai_report", None)
    clear_ai_state()


# 初始化语言状态，确保首次加载有默认值
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

# 侧边栏：系统环境信息 + 语言切换器
with st.sidebar:
    # 语言切换组件：置于侧边栏顶部，直接使用 radio 返回值，避免额外 session_state 更新导致的滞后渲染
    lang = st.radio(
        "Language / 语言",
        ["English", "中文"],
        index=0 if st.session_state["lang"] == "English" else 1,
        key="lang_selector",
        on_change=clear_ai_state,
    )
    st.session_state["lang"] = lang

    t = TEXT[lang]

    st.header(t["sys_env"])

    current_os = platform.system()
    st.success(f"OS: {current_os}")

    root_path = get_project_root()
    st.info(f"Project Root: {root_path}")

    mock_path = get_mock_data_path()
    st.info(f"Mock Data Path: {mock_path}")

    st.divider()
    st.caption(t["cross_platform"])

    # AI Engine Configuration
    st.divider()
    st.header("AI Engine Configuration")

    MODEL_OPTIONS = {
        "Local (Ollama)": {"api_base": "http://localhost:11434/v1", "api_key": "ollama_local"},
        "DeepSeek API": {"api_base": "https://api.deepseek.com/v1", "api_key": ""},
        "OpenAI API": {"api_base": "https://api.openai.com/v1", "api_key": ""},
    }

    model_choice = st.selectbox(
        "Select Model / 选择模型",
        list(MODEL_OPTIONS.keys()),
        index=0 if st.session_state.get("model_choice") in MODEL_OPTIONS
        else list(MODEL_OPTIONS.keys()).index(st.session_state.get("model_choice", "Local (Ollama)")),
        key="model_selector",
    )
    st.session_state["model_choice"] = model_choice

    if model_choice == "Local (Ollama)":
        st.success("🟢 100% Private: Data stays on your device.")
        st.session_state["api_key"] = "ollama_local"
        st.session_state["api_base"] = MODEL_OPTIONS[model_choice]["api_base"]
    else:
        st.warning("🔴 Warning: Financial data will be sent to external cloud servers.")
        user_key = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.get("api_key", ""),
            key="api_key_input",
        )
        st.session_state["api_key"] = user_key
        st.session_state["api_base"] = MODEL_OPTIONS[model_choice]["api_base"]

    st.divider()
    st.header("Control Panel / 控制面板")
    uploaded_file = st.file_uploader(t["uploader_label"], type=["xlsx"], on_change=reset_all_state)


# 语言状态已在侧边栏中确定，此处重新获取当前语言对应的文本字典
# 并将 t 提升到外层作用域，供后续 UI 渲染使用
t = TEXT[st.session_state["lang"]]

# 初始化引擎配置默认值
if "model_choice" not in st.session_state:
    st.session_state["model_choice"] = "Local (Ollama)"
if "api_key" not in st.session_state:
    st.session_state["api_key"] = "ollama_local"
if "api_base" not in st.session_state:
    st.session_state["api_base"] = "http://localhost:11434/v1"

st.title("⚡ AuditCore 智能穿透审计系统")
st.caption("EvidenceGraph-powered multi-agent audit control plane")


# 优先级纠正：有上传文件时，以内存中的上传对象为唯一数据源
# 禁止在有上传文件的情况下，去读取 mock_data 文件夹里的本地同名文件
if uploaded_file is not None:
    loader = AuditDataLoader()
    try:
        df = loader.load_excel(uploaded_file)
        st.session_state["df"] = df
        st.session_state["file_name"] = uploaded_file.name
    except Exception as e:
        st.error(f"{t['failed_process']}: {e}")
        st.stop()

if st.session_state.get("df") is not None:
    df = st.session_state["df"]

    # 动态列名重命名：确保后续规则扫描能适配不同表头
    # 在数据加载后，立即使用候选列名列表匹配并重命名第一个找到的列为 'Amount'
    amount_candidates = ["data", "Amount", "金额", "数值"]
    for candidate in amount_candidates:
        if candidate in df.columns:
            if candidate != "Amount":
                df = df.rename(columns={candidate: "Amount"})
                st.session_state["df"] = df
            break

    file_label = uploaded_file.name if uploaded_file is not None else st.session_state.get("file_name", "unknown")
    st.success(f"{t['file_loaded']}: {file_label} — {len(df)} {t['rows']}")

    # 异常扫描按钮进入侧边栏控制面板，主区只负责展示结果。
    with st.sidebar:
        if st.button(t["run_scan"], use_container_width=True):
            current_df = st.session_state["df"]
            rule_agent = RuleAgent()
            result = rule_agent.build_scan_result(current_df)
            st.session_state["scan_results"] = result
            st.session_state.pop("ai_report", None)

    # 读取扫描结果，无论当前是按钮点击还是页面重运行
    if st.session_state.get("scan_results") is not None:
        result = st.session_state["scan_results"]
        anomalies = result["anomalies"]
        stats = result["stats"]

        metric_graph = ensure_current_evidence_graph(st.session_state.get("evidence_graph", EvidenceGraph()))
        global_consistency_score = metric_graph.calculate_consistency_score()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="全局一致性评分", value=f"{global_consistency_score:.2f}")
        with col2:
            st.metric(label=t["total_records"], value=stats["total_records"])
        with col3:
            st.metric(label=t["anomalies_detected"], value=stats["anomaly_count"])
        with col4:
            if stats["max_amount"] is not None:
                st.metric(label="涉案总金额", value=f"{stats['max_amount']:,.2f}")
            else:
                st.metric(label="图节点数", value=len(metric_graph.nodes))

        tab_dashboard, tab_war_room, tab_graph, tab_report = st.tabs(
            ["📊 审计总控台", "🤖 智能体博弈", "🕸️ 熔断控制室", "📄 最终工作底稿"]
        )

        with tab_dashboard:
            with st.expander("查看原始凭证数据", expanded=False):
                st.dataframe(
                    st.session_state["df"],
                    use_container_width=True,
                    height=300,
                )

            found_any = False
            for label, anomaly_df in anomalies.items():
                if not anomaly_df.empty:
                    found_any = True
                    with st.expander(f"{t['anomaly_view']} — {label} ({len(anomaly_df)} {t['anomaly_detected']})", expanded=True):
                        st.error(f"{label}: {len(anomaly_df)} {t['anomaly_detected']}")
                        st.dataframe(anomaly_df, use_container_width=True)

            if not found_any:
                st.success(t["no_anomalies"])

        # AI Agent 多 Agent 串行审计模块
        # 数据流转：初级审计员先出报告（JSON），反方 Agent 接收初级报告后输出 JSON 复核
        with st.sidebar:
            st.divider()
            st.subheader(t["ai_opinion"])
            generate_report_clicked = st.button(t["generate_report"], use_container_width=True)

        # 统一按钮：一次点击触发串行执行，保证两份报告在同一轮渲染中产出
        if generate_report_clicked:
            with st.spinner("Agents are analyzing..."):
                try:
                    st.session_state.pop("conflict_arbitration", None)
                    st.session_state.pop("manual_final_confirmation", None)

                    # 引擎路由验证：云端模型需要用户提供 API Key
                    api_key = st.session_state.get("api_key", "")
                    model_choice = st.session_state.get("model_choice", "Local (Ollama)")
                    if model_choice != "Local (Ollama)" and not api_key.strip():
                        raise RuntimeError(f"API Key is required for {model_choice}. Please enter your key in the sidebar.")

                    evidence_graph = EvidenceGraph()
                    scan_result = st.session_state["scan_results"]
                    for i, finding in enumerate(scan_result["rule_findings"]):
                        evidence_graph.add_node(
                            EvidenceNode(
                                node_id=f"rule_fact_{i}",
                                node_type="RuleFinding",
                                content=finding.summary,
                            )
                        )

                    # 第一阶段：JuniorAuditorAgent 生成初级审计意见（JSON 字符串）
                    junior = JuniorAuditorAgent(
                        lang=st.session_state["lang"],
                        api_key=api_key,
                        api_base=st.session_state["api_base"],
                    )
                    junior_raw = junior.generate_report(anomalies, stats)

                    # JSON 解析逻辑：大模型可能偶尔输出不完美 JSON，需加防护
                    try:
                        junior_data = json.loads(junior_raw)
                        junior_analysis = junior_data.get("analysis", "No analysis provided.")
                        junior_score = int(junior_data.get("risk_score", 50))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        junior_analysis = f"[JSON parse failed, raw output]: {junior_raw}"
                        junior_score = 50

                    # 第二阶段：FactCheckAgent 对初级结论做事实核查。
                    # 为兼容现有 Partner 阶段，这里临时映射为旧版 challenger 文本与分值。
                    fact_checker = FactCheckAgent(
                        lang=st.session_state["lang"],
                        api_key=api_key,
                        api_base=st.session_state["api_base"],
                    )
                    fact_check_raw = fact_checker.generate_fact_check(
                        anomalies,
                        stats,
                        junior_analysis,
                        junior_score,
                    )

                    # JSON 解析逻辑：事实核查阶段先标准化到专利契约，再兼容旧版字段。
                    try:
                        fact_check_data = json.loads(fact_check_raw)
                        fact_check_result = FactCheckResult.from_payload(fact_check_data)
                    except (json.JSONDecodeError, TypeError, ValueError):
                        fact_check_result = FactCheckResult.from_payload(
                            payload=None,
                            fallback_analysis=f"[JSON parse failed, raw output]: {fact_check_raw}",
                        )

                    challenger_rebuttal = fact_check_result.analysis
                    challenger_score = fact_check_result.to_legacy_challenger_score()

                    junior_node_id = "junior_conclusion"
                    challenger_node_id = "challenger_conclusion"
                    evidence_graph.add_node(
                        EvidenceNode(
                            node_id=junior_node_id,
                            node_type="JuniorConclusion",
                            content=junior_analysis,
                            metadata={"risk_score": junior_score},
                        )
                    )
                    evidence_graph.add_node(
                        EvidenceNode(
                            node_id=challenger_node_id,
                            node_type="ChallengerConclusion",
                            content=challenger_rebuttal,
                            metadata={
                                "risk_score": challenger_score,
                                "support_score": fact_check_result.support_score,
                                "conflict_score": fact_check_result.conflict_score,
                            },
                        )
                    )
                    if fact_check_result.conflict_score > fact_check_result.support_score:
                        relation = "conflict"
                        weight = fact_check_result.conflict_score
                    else:
                        relation = "support"
                        weight = fact_check_result.support_score
                    evidence_graph.add_edge(
                        EvidenceEdge(
                            source_id=challenger_node_id,
                            target_id=junior_node_id,
                            relation=relation,
                            weight=weight,
                        )
                    )

                    # 结构化数据存入 session_state 供 UI 渲染使用
                    st.session_state["junior_analysis"] = junior_analysis
                    st.session_state["junior_score"] = junior_score
                    st.session_state["challenger_rebuttal"] = challenger_rebuttal
                    st.session_state["challenger_score"] = challenger_score
                    st.session_state["fact_check_analysis"] = fact_check_result.analysis
                    st.session_state["fact_check_support_score"] = fact_check_result.support_score
                    st.session_state["fact_check_conflict_score"] = fact_check_result.conflict_score
                    st.session_state["evidence_graph"] = evidence_graph
                    st.session_state["patent_contracts"] = {
                        "rule_findings": [
                            asdict(
                                RuleFinding(
                                    label=label,
                                    record_count=len(df),
                                    summary=f"{label}: {len(df)} record(s)",
                                )
                            )
                            for label, df in anomalies.items()
                            if not df.empty
                        ],
                        "fact_check_result": asdict(fact_check_result),
                    }

                    # 第三阶段：SeniorPartnerAgent 综合两方报告做出最终裁决
                    partner = SeniorPartnerAgent(
                        lang=st.session_state["lang"],
                        api_key=api_key,
                        api_base=st.session_state["api_base"],
                    )
                    partner_raw = partner.generate_verdict(
                        total_records=stats["total_records"],
                        anomaly_count=stats["anomaly_count"],
                        junior_report=junior_analysis,
                        junior_score=junior_score,
                        challenger_rebuttal=challenger_rebuttal,
                        challenger_score=challenger_score,
                    )

                    try:
                        partner_data = json.loads(partner_raw)
                        partner_verdict = partner_data.get("final_verdict", "Unknown")
                        partner_risk = int(partner_data.get("final_risk_score", 50))
                        partner_reasoning = partner_data.get("reasoning", "No reasoning provided.")
                        partner_action = partner_data.get("action_item", "No action specified.")
                    except (json.JSONDecodeError, TypeError, ValueError):
                        partner_verdict = "Unknown"
                        partner_risk = 50
                        partner_reasoning = f"[JSON parse failed, raw output]: {partner_raw}"
                        partner_action = ""

                    st.session_state["partner_verdict"] = partner_verdict
                    st.session_state["partner_risk"] = partner_risk
                    st.session_state["partner_reasoning"] = partner_reasoning
                    st.session_state["partner_action"] = partner_action
                    st.rerun()
                except Exception as e:
                    st.session_state["junior_analysis"] = f"[Error] {e}"
                    st.session_state["junior_score"] = 0
                    st.session_state["challenger_rebuttal"] = ""
                    st.session_state["challenger_score"] = 0
                    st.session_state["fact_check_analysis"] = ""
                    st.session_state["fact_check_support_score"] = 0.0
                    st.session_state["fact_check_conflict_score"] = 0.0
                    st.session_state["evidence_graph"] = EvidenceGraph()
                    st.session_state["patent_contracts"] = {}
                    st.session_state["partner_verdict"] = "Unknown"
                    st.session_state["partner_risk"] = 0
                    st.session_state["partner_reasoning"] = f"[Error] {e}"
                    st.session_state["partner_action"] = ""

        # 第三阶段渲染：使用企业级 Dashboard Tabs 承载最终状态、智能体博弈、熔断和底稿导出。
        if st.session_state.get("partner_verdict") is not None:
            evidence_graph = ensure_current_evidence_graph(st.session_state.get("evidence_graph", EvidenceGraph()))
            st.session_state["evidence_graph"] = evidence_graph
            global_consistency_score = evidence_graph.calculate_consistency_score()

            CONSISTENCY_THRESHOLD = 0.80
            current_state = STATE_INIT

            if global_consistency_score >= CONSISTENCY_THRESHOLD:
                current_state = STATE_FINAL_VERDICT
            else:
                current_state = STATE_ROLLBACK_REVIEW
            if st.session_state.get("manual_final_confirmation"):
                current_state = STATE_FINAL_VERDICT

            disputed_edges = [
                edge
                for edge in evidence_graph.edges
                if edge.relation.strip().lower() in {"conflict", "conflicts", "冲突"}
            ]
            if not disputed_edges:
                disputed_edges = evidence_graph.edges

            dispute_rows = []
            for edge in disputed_edges:
                source_node = evidence_graph.nodes.get(edge.source_id)
                target_node = evidence_graph.nodes.get(edge.target_id)
                dispute_rows.append(
                    {
                        "source_node": edge.source_id,
                        "source_type": source_node.node_type if source_node else "Unknown",
                        "target_node": edge.target_id,
                        "target_type": target_node.node_type if target_node else "Unknown",
                        "relation": edge.relation,
                        "weight": f"{edge.weight:.2f}",
                        "source_content": source_node.content if source_node else "",
                        "target_content": target_node.content if target_node else "",
                    }
                )

            with tab_dashboard:
                with st.container(border=True):
                    st.subheader("专利防御层：中间表示控制装置")

                    if current_state == STATE_FINAL_VERDICT:
                        if st.session_state.get("manual_final_confirmation"):
                            st.success("✅ 冲突仲裁完成：状态机经人工最终确认推进至最终合伙人裁决阶段。")
                            arbitration_text = st.session_state.get("conflict_arbitration", "")
                            if arbitration_text:
                                st.info(arbitration_text)
                        else:
                            st.success("✅ 穿透审计通过：数据一致性达标，状态机安全推进至最终合伙人裁决阶段。")
                    else:
                        st.error("🚨 专利熔断机制触发：检测到审计事实存在严重冲突，一致性评分低于阈值！")

                if current_state == STATE_FINAL_VERDICT:
                    with st.container(border=True):
                        st.subheader(t["partner_verdict"])

                        verdict_raw = st.session_state["partner_verdict"]
                        partner_risk = st.session_state.get("partner_risk", 0)
                        partner_reasoning = st.session_state.get("partner_reasoning", "")
                        partner_action = st.session_state.get("partner_action", "")
                        lang_key = st.session_state["lang"]
                        verdict_display = VERDICT_MAP.get(lang_key, {}).get(verdict_raw, verdict_raw)

                        if verdict_raw == "True Anomaly":
                            st.error(f"🔴 **Final Verdict: :red[{verdict_display}]**")
                        elif verdict_raw == "False Positive":
                            st.success(f"🟢 **Final Verdict: :green[{verdict_display}]**")
                        else:
                            st.warning(f"⚪ **Final Verdict: {verdict_display}**")

                        cols_partner = st.columns(2)
                        with cols_partner[0]:
                            st.metric(label=t["partner_risk"], value=f"{partner_risk}/100")
                        with cols_partner[1]:
                            st.caption(t["partner_action"])
                            st.markdown(f"**:pushpin: {t['action_prefix']}{partner_action}**")

                        st.markdown(f"**{t['partner_reasoning']}:**")
                        if partner_reasoning.startswith("[Error]") or partner_reasoning.startswith("[JSON"):
                            st.error(partner_reasoning)
                        elif partner_reasoning == "":
                            st.warning(t["partner_not_available"])
                        else:
                            st.info(partner_reasoning)

            with tab_war_room:
                with st.container(border=True):
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.subheader(t["junior_finding"])
                        st.metric(label=t["junior_risk"], value=f"{st.session_state.get('junior_score', 0)}/100")
                        analysis_text = st.session_state.get("junior_analysis", "")
                        if analysis_text.startswith("[Error]"):
                            st.error(analysis_text)
                        else:
                            st.info(analysis_text)
                    with right_col:
                        st.subheader(t["challenger_review"])
                        junior_prev = st.session_state.get("junior_score", 50)
                        challenger_prev = st.session_state.get("challenger_score", 30)
                        st.metric(label=t["challenger_risk"], value=f"{challenger_prev}/100", delta=f"{challenger_prev - junior_prev}")
                        fact_support = st.session_state.get("fact_check_support_score")
                        fact_conflict = st.session_state.get("fact_check_conflict_score")
                        if fact_support is not None and fact_conflict is not None:
                            st.caption(f"Support Score: {fact_support:.2f} | Conflict Score: {fact_conflict:.2f}")
                        rebuttal_text = st.session_state.get("challenger_rebuttal", "")
                        if rebuttal_text == "":
                            st.warning(t["challenger_not_available"])
                        elif rebuttal_text.startswith("[Error]"):
                            st.error(rebuttal_text)
                        else:
                            st.warning(rebuttal_text)

                    final_score = st.session_state.get("challenger_score", 50)
                    if final_score > 60:
                        st.error(t["high_risk"])
                    else:
                        st.success(t["low_risk"])

            with tab_graph:
                with st.container(border=True):
                    st.subheader("图谱与熔断控制")
                    st.metric(
                        label="Global Consistency Score",
                        value=f"{global_consistency_score:.2f}",
                    )

                    if current_state == STATE_ROLLBACK_REVIEW:
                        st.error("🚨 专利熔断机制触发：检测到审计事实存在严重冲突，一致性评分低于阈值！")
                        st.warning("状态机已回退至 STATE_ROLLBACK_REVIEW：请先完成冲突事实质证，再推进最终合伙人裁决。")
                    else:
                        st.success("✅ DAG 状态机当前处于 STATE_FINAL_VERDICT。")

                    if dispute_rows:
                        st.dataframe(dispute_rows, use_container_width=True)
                    else:
                        st.info("当前证据图尚未形成可展示的质证边，请重新运行多 Agent 审计流程。")

                    if current_state == STATE_ROLLBACK_REVIEW and st.button("⚡ 启动 FactCheckAgent 深度仲裁"):
                        with st.spinner("FactCheckAgent is resolving conflicts..."):
                            try:
                                api_key = st.session_state.get("api_key", "")
                                model_choice = st.session_state.get("model_choice", "Local (Ollama)")
                                if model_choice != "Local (Ollama)" and not api_key.strip():
                                    raise RuntimeError(f"API Key is required for {model_choice}. Please enter your key in the sidebar.")

                                junior_node = evidence_graph.nodes.get("junior_conclusion")
                                challenger_node = evidence_graph.nodes.get("challenger_conclusion")
                                fact_checker = FactCheckAgent(
                                    lang=st.session_state["lang"],
                                    api_key=api_key,
                                    api_base=st.session_state["api_base"],
                                )
                                arbitration_text = fact_checker.resolve_conflicts(
                                    conflict_edges=disputed_edges,
                                    junior_node=junior_node,
                                    challenger_node=challenger_node,
                                )
                                st.session_state["conflict_arbitration"] = arbitration_text
                                st.session_state["manual_final_confirmation"] = True
                                st.rerun()
                            except Exception as e:
                                st.error(f"FactCheckAgent 深度仲裁失败: {e}")

            with tab_report:
                with st.container(border=True):
                    st.subheader("底稿导出中心")
                    if current_state == STATE_FINAL_VERDICT:
                        report_md = evidence_graph.export_working_paper()
                        with st.expander("📄 查看完整审计工作底稿", expanded=True):
                            st.markdown(report_md)
                        st.download_button(
                            label="💾 下载底稿 (.md)",
                            data=report_md,
                            file_name="audit_working_paper.md",
                            mime="text/markdown",
                        )
                    else:
                        st.warning("当前状态未进入最终合伙人确认阶段，底稿导出已被状态机暂缓。")
