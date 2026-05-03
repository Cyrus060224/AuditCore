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

        # AI Agent 多 Agent 串行审计模块
        # 数据流转：初级审计员先出报告（JSON），反方 Agent 接收初级报告后输出 JSON 复核
        st.subheader("AI Agent's Preliminary Opinion")

        # 统一按钮：一次点击触发串行执行，保证两份报告在同一轮渲染中产出
        if st.button("Generate AI Report"):
            with st.spinner("Agents are analyzing..."):
                try:
                    # 第一阶段：JuniorAuditorAgent 生成初级审计意见（JSON 字符串）
                    junior = JuniorAuditorAgent()
                    junior_raw = junior.generate_report(anomalies, stats)

                    # JSON 解析逻辑：大模型可能偶尔输出不完美 JSON，需加防护
                    try:
                        junior_data = json.loads(junior_raw)
                        junior_analysis = junior_data.get("analysis", "No analysis provided.")
                        junior_score = int(junior_data.get("risk_score", 50))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        # 解析失败时回退到默认值，避免程序崩溃
                        junior_analysis = f"[JSON parse failed, raw output]: {junior_raw}"
                        junior_score = 50

                    # 第二阶段：数据从 scan_results + junior_report 流入 ChallengerAgent
                    # ChallengerAgent 接收总记录数、异常文本、初级报告作为输入
                    anomaly_text = junior._format_anomalies(anomalies)
                    challenger = ChallengerAgent()
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
                        # 解析失败时回退到默认值，避免程序崩溃
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
                st.subheader("Junior Auditor's Finding")
                # 量化分数展示：初审风险分
                st.metric(label="Junior Risk Score", value=f"{st.session_state['junior_score']}/100")
                analysis_text = st.session_state["junior_analysis"]
                if analysis_text.startswith("[Error]"):
                    st.error(analysis_text)
                else:
                    st.info(analysis_text)
            with right_col:
                st.subheader("Challenger's Review")
                # 量化分数展示：复核后风险分及差值（delta 为负表示风险下调）
                junior_prev = st.session_state.get("junior_score", 50)
                challenger_prev = st.session_state.get("challenger_score", 30)
                st.metric(label="Challenger Risk Score", value=f"{challenger_prev}/100", delta=f"{challenger_prev - junior_prev}")
                rebuttal_text = st.session_state.get("challenger_rebuttal", "")
                if rebuttal_text == "":
                    st.warning("Challenger report not available.")
                elif rebuttal_text.startswith("[Error]"):
                    st.error(rebuttal_text)
                else:
                    st.info(rebuttal_text)

            # 总结论断：基于 Challenger 调整后的分数决定风险级别
            final_score = st.session_state.get("challenger_score", 50)
            if final_score > 60:
                st.error("HIGH RISK: Immediate manual intervention recommended.")
            else:
                st.success("LOW RISK: Likely normal business write-offs.")
