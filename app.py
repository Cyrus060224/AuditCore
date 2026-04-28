"""
Streamlit 主入口（MVP 版本）。
侧边栏展示系统环境信息，主界面接收审计文件上传、数据预览及异常扫描。
"""

import platform
import streamlit as st
from core.utils import get_project_root, get_mock_data_path
from core.data_loader import AuditDataLoader

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
        st.session_state.pop("scan_done", None)
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

    # 数据概览
    st.success(f"File loaded: {uploaded_file.name if uploaded_file is not None else st.session_state.get('file_name')} — {len(df)} rows")

    st.subheader("Data Preview")
    st.write(f"Total rows: {len(df)}")
    st.dataframe(df.head(5))

    # 异常扫描按钮：仅在数据成功加载后渲染
    st.subheader("Preliminary Scan")
    if st.button("Run Preliminary Scan"):
        loader = AuditDataLoader()
        anomalies = loader.basic_scan(df)

        found_any = False
        for label, anomaly_df in anomalies.items():
            if not anomaly_df.empty:
                found_any = True
                st.error(f"**{label}**: {len(anomaly_df)} record(s) detected")
                st.dataframe(anomaly_df)

        if not found_any:
            st.success("No anomalies found in preliminary scan.")
