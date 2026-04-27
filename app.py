import platform
import streamlit as st
from core.utils import get_project_root, get_mock_data_path

st.set_page_config(page_title="AuditCore", page_icon=":clipboard:", layout="wide")

st.title("AuditCore - Multi-Agent Audit System MVP")

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

uploaded_file = st.file_uploader("Upload audit file for analysis", type=["xlsx", "pdf"])

if uploaded_file is not None:
    st.success(f"File received: {uploaded_file.name} ({uploaded_file.size} bytes)")
