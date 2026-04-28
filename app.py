"""
Streamlit 主入口（MVP 版本）。
侧边栏展示系统环境信息，主界面接收审计文件上传、数据预览及异常扫描。
"""

import platform
import streamlit as st
from core.utils import get_project_root, get_mock_data_path
from core.data_loader import AuditDataLoader
from agents.auditor_agent import JuniorAuditorAgent

st.set_page_config(page_title="AuditCore", page_icon=":clipboard:", layout="wide")

st.title("AuditCore - Multi-Agent Audit System MVP")

# 侧边栏：系统环境信息，用于跨平台路径验证
with st.sidebar:
    st.header("System Environment")

    current_os = platform.system()
    st.success(f"OS: {current_os}")

    root_path = get_project_root()
    st.info(f"Project Root: {root_path}")

    mock_path = get_mock_data_path()
    st.info(f"Mock Data Path: {mock_path}")

    st.divider()
    st.caption("Cross-platform path handler active")


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


# 主界面：文件上传
# on_change=reset_all_state 确保只要用户重新选择文件或点击叉号，
# 所有旧状态立即物理抹除，打破 Streamlit 文件缓存机制
uploaded_file = st.file_uploader("Upload audit file (.xlsx)", type=["xlsx"], on_change=reset_all_state)

# 优先级纠正：有上传文件时，以内存中的上传对象为唯一数据源
# 禁止在有上传文件的情况下，去读取 mock_data 文件夹里的本地同名文件
if uploaded_file is not None:
    loader = AuditDataLoader()
    try:
        df = loader.load_excel(uploaded_file)
        st.session_state["df"] = df
        st.session_state["file_name"] = uploaded_file.name
    except Exception as e:
        st.error(f"Failed to process file: {e}")
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
    st.success(f"File loaded: {file_label} — {len(df)} rows")

    # 数据概览
    # Data Preview 直接读取 st.session_state["df"]，df 为空时不显示
    st.subheader("Data Preview")
    st.write(f"Total rows: {len(df)}")
    # 让 Streamlit 自己处理滚动条，展示全量数据
    st.dataframe(
    st.session_state["df"], 
    use_container_width=True, # 让表格宽度自适应网页填满
    height=300 # 设置一个固定高度，超出 300 像素会自动出现滚动条
)

    # 异常扫描按钮
    st.subheader("Preliminary Scan")
    if st.button("Run Preliminary Scan"):
        # 按钮点击时重新获取当前最准确的 df
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
            st.metric(label="Total Records", value=stats["total_records"])
        with cols[1]:
            st.metric(label="Anomalies Detected", value=stats["anomaly_count"])
        with cols[2]:
            if stats["max_amount"] is not None:
                st.metric(label="Max Amount", value=f"{stats['max_amount']:,.2f}")
            else:
                st.metric(label="Max Amount", value="N/A")

        # 异常详情折叠面板
        found_any = False
        for label, anomaly_df in anomalies.items():
            if not anomaly_df.empty:
                found_any = True
                with st.expander(f"View Anomaly Details — {label} ({len(anomaly_df)} record(s))", expanded=True):
                    st.error(f"{label}: {len(anomaly_df)} record(s) detected")
                    st.dataframe(anomaly_df)

        if not found_any:
            st.success("No anomalies found in preliminary scan.")

        # AI Agent 审计意见模块
        st.subheader("AI Agent's Preliminary Opinion")

        if st.button("Generate AI Report"):
            # 调用 Agent 引擎，异常数据从 scan_results 中流转至 Agent
            with st.spinner("Agent is analyzing..."):
                try:
                    agent = JuniorAuditorAgent()
                    report = agent.generate_report(anomalies, stats)
                    st.session_state["ai_report"] = report
                except Exception as e:
                    st.session_state["ai_report"] = f"[Error] {e}"

        # 展示 Agent 报告，页面重运行时从 session_state 恢复
        if st.session_state.get("ai_report") is not None:
            report_text = st.session_state["ai_report"]
            if report_text.startswith("[Error]"):
                st.error(report_text)
            else:
                st.info(report_text)
