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

# 主界面：文件上传
uploaded_file = st.file_uploader("Upload audit file (.xlsx)", type=["xlsx"])

# 检测到新文件上传时，清除旧缓存
if uploaded_file is not None:
    if st.session_state.get("file_name") != uploaded_file.name:
        st.session_state.pop("df", None)
        st.session_state.pop("scan_result", None)
        st.session_state.pop("agent_report", None)
        st.session_state["file_name"] = uploaded_file.name

# 成功加载的 DataFrame 持久化到 session_state，
# 防止按钮点击后页面重运行导致数据丢失
if "df" not in st.session_state and uploaded_file is not None:
    loader = AuditDataLoader()

    try:
        df = loader.load_excel(uploaded_file)
        st.session_state["df"] = df
    except Exception as e:
        st.error(f"Failed to process file: {e}")
        st.stop()

if st.session_state.get("df") is not None:
    df = st.session_state["df"]

    file_label = uploaded_file.name if uploaded_file is not None else st.session_state.get("file_name")
    st.success(f"File loaded: {file_label} — {len(df)} rows")

    # 数据概览
    st.subheader("Data Preview")
    st.write(f"Total rows: {len(df)}")
    st.dataframe(df.head(5))

    # 异常扫描按钮：仅在数据成功加载后渲染
    st.subheader("Preliminary Scan")
    if st.button("Run Preliminary Scan"):
        loader = AuditDataLoader()
        result = loader.basic_scan(df)
        st.session_state["scan_result"] = result
        st.session_state.pop("agent_report", None)

    # 读取扫描结果，无论当前是按钮点击还是页面重运行
    if st.session_state.get("scan_result") is not None:
        result = st.session_state["scan_result"]
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
            # 调用 Agent 引擎，异常数据从 scan_result 中流转至 Agent
            with st.spinner("Agent is analyzing..."):
                try:
                    agent = JuniorAuditorAgent()
                    report = agent.generate_report(anomalies, stats)
                    st.session_state["agent_report"] = report
                except Exception as e:
                    st.session_state["agent_report"] = f"[Error] {e}"

        # 展示 Agent 报告，页面重运行时从 session_state 恢复
        if st.session_state.get("agent_report") is not None:
            report_text = st.session_state["agent_report"]
            if report_text.startswith("[Error]"):
                st.error(report_text)
            else:
                st.info(report_text)
