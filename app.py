# -*- coding: utf-8 -*-
"""
Streamlit 主入口（MVP 版本）。
侧边栏展示系统环境信息，主界面接收审计文件上传、数据预览及异常扫描。
"""

import json
import platform
import streamlit as st
from core.utils import get_project_root, get_mock_data_path
from core.data_loader import AuditDataLoader
from agents.auditor_agent import JuniorAuditorAgent
from agents.challenger_agent import ChallengerAgent

st.set_page_config(page_title="AuditCore", page_icon=":clipboard:", layout="wide")

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
    },
}


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

# 语言状态已在侧边栏中确定，此处重新获取当前语言对应的文本字典
# 并将 t 提升到外层作用域，供后续 UI 渲染使用
t = TEXT[st.session_state["lang"]]
st.title(t["title"])


# 主界面：文件上传
# on_change=reset_all_state 确保只要用户重新选择文件或点击叉号，
# 所有旧状态立即物理抹除，打破 Streamlit 文件缓存机制
uploaded_file = st.file_uploader(t["uploader_label"], type=["xlsx"], on_change=reset_all_state)

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

    # 动态列名重命名：确保后续 basic_scan 能适配不同表头
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

    # 数据概览
    # Data Preview 直接读取 st.session_state["df"]，df 为空时不显示
    st.subheader(t["data_preview"])
    st.write(f"{t['total_rows']}: {len(df)}")
    st.dataframe(
        st.session_state["df"],
        use_container_width=True,
        height=300,
    )

    # 异常扫描按钮
    st.subheader(t["preliminary_scan"])
    if st.button(t["run_scan"]):
        loader = AuditDataLoader()
        current_df = st.session_state["df"]
        result = loader.basic_scan(current_df)
        st.session_state["scan_results"] = result
        st.session_state.pop("ai_report", None)

    # 读取扫描结果，无论当前是按钮点击还是页面重运行
    if st.session_state.get("scan_results") is not None:
        result = st.session_state["scan_results"]
        anomalies = result["anomalies"]
        stats = result["stats"]

        # 仪表盘指标展示
        cols = st.columns(3)
        with cols[0]:
            st.metric(label=t["total_records"], value=stats["total_records"])
        with cols[1]:
            st.metric(label=t["anomalies_detected"], value=stats["anomaly_count"])
        with cols[2]:
            if stats["max_amount"] is not None:
                st.metric(label=t["max_amount"], value=f"{stats['max_amount']:,.2f}")
            else:
                st.metric(label=t["max_amount"], value="N/A")

        # 异常详情折叠面板
        found_any = False
        for label, anomaly_df in anomalies.items():
            if not anomaly_df.empty:
                found_any = True
                with st.expander(f"{t['anomaly_view']} — {label} ({len(anomaly_df)} {t['anomaly_detected']})", expanded=True):
                    st.error(f"{label}: {len(anomaly_df)} {t['anomaly_detected']}")
                    st.dataframe(anomaly_df)

        if not found_any:
            st.success(t["no_anomalies"])

        # AI Agent 多 Agent 串行审计模块
        # 数据流转：初级审计员先出报告（JSON），反方 Agent 接收初级报告后输出 JSON 复核
        st.subheader(t["ai_opinion"])

        # 统一按钮：一次点击触发串行执行，保证两份报告在同一轮渲染中产出
        if st.button(t["generate_report"]):
            with st.spinner("Agents are analyzing..."):
                try:
                    # 第一阶段：JuniorAuditorAgent 生成初级审计意见（JSON 字符串）
                    # 将当前语言状态传递给 Agent，用于控制大模型输出语言
                    junior = JuniorAuditorAgent(lang=st.session_state["lang"])
                    junior_raw = junior.generate_report(anomalies, stats)

                    # JSON 解析逻辑：大模型可能偶尔输出不完美 JSON，需加防护
                    try:
                        junior_data = json.loads(junior_raw)
                        junior_analysis = junior_data.get("analysis", "No analysis provided.")
                        junior_score = int(junior_data.get("risk_score", 50))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        junior_analysis = f"[JSON parse failed, raw output]: {junior_raw}"
                        junior_score = 50

                    # 第二阶段：数据从 scan_results + junior_report 流入 ChallengerAgent
                    anomaly_text = junior._format_anomalies(anomalies)
                    # 将当前语言状态传递给反方 Agent
                    challenger = ChallengerAgent(lang=st.session_state["lang"])
                    challenger_raw = challenger.generate_review(
                        total_records=stats["total_records"],
                        anomaly_text=anomaly_text,
                        junior_report=junior_analysis,
                    )

                    # JSON 解析逻辑：同样对反方输出做容错处理
                    try:
                        challenger_data = json.loads(challenger_raw)
                        challenger_rebuttal = challenger_data.get("rebuttal", "No rebuttal provided.")
                        challenger_score = int(challenger_data.get("adjusted_risk_score", 30))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        challenger_rebuttal = f"[JSON parse failed, raw output]: {challenger_raw}"
                        challenger_score = 30

                    # 结构化数据存入 session_state 供 UI 渲染使用
                    st.session_state["junior_analysis"] = junior_analysis
                    st.session_state["junior_score"] = junior_score
                    st.session_state["challenger_rebuttal"] = challenger_rebuttal
                    st.session_state["challenger_score"] = challenger_score
                except Exception as e:
                    st.session_state["junior_analysis"] = f"[Error] {e}"
                    st.session_state["junior_score"] = 0
                    st.session_state["challenger_rebuttal"] = ""
                    st.session_state["challenger_score"] = 0

        # 左右两栏对比渲染：初级审计员 vs 反方复核
        if st.session_state.get("junior_analysis") is not None:
            left_col, right_col = st.columns(2)
            with left_col:
                st.subheader(t["junior_finding"])
                st.metric(label=t["junior_risk"], value=f"{st.session_state['junior_score']}/100")
                analysis_text = st.session_state["junior_analysis"]
                if analysis_text.startswith("[Error]"):
                    st.error(analysis_text)
                else:
                    st.info(analysis_text)
            with right_col:
                st.subheader(t["challenger_review"])
                junior_prev = st.session_state.get("junior_score", 50)
                challenger_prev = st.session_state.get("challenger_score", 30)
                st.metric(label=t["challenger_risk"], value=f"{challenger_prev}/100", delta=f"{challenger_prev - junior_prev}")
                rebuttal_text = st.session_state.get("challenger_rebuttal", "")
                if rebuttal_text == "":
                    st.warning(t["challenger_not_available"])
                elif rebuttal_text.startswith("[Error]"):
                    st.error(rebuttal_text)
                else:
                    st.info(rebuttal_text)

            # 总结论断：基于 Challenger 调整后的分数决定风险级别
            final_score = st.session_state.get("challenger_score", 50)
            if final_score > 60:
                st.error(t["high_risk"])
            else:
                st.success(t["low_risk"])
