# AuditCore Code Wiki

## 项目概览

**AuditCore** 是一个基于多 Agent 架构的智能审计系统 MVP（最小可行产品）。系统采用 Streamlit 作为 Web 界面框架，通过三个独立的 AI Agent（初级审计员、反方审计员、高级合伙人）串联协作，对用户上传的 Excel 财务数据进行自动化审计分析。

### 核心特性

- **多 Agent 串行审计**：Junior Auditor → Challenger → Senior Partner 三阶段审计流程
- **多模型路由**：支持 Ollama（本地私有）、DeepSeek API、OpenAI API
- **跨平台兼容**：统一使用 pathlib 处理路径，兼容 Windows/macOS/Linux
- **国际化支持**：中英文双语界面，动态切换
- **RAG 知识检索**：基于 PDF 审计准则的本地向量知识库（Chroma）

---

## 项目结构

```
AuditCore/
├── .streamlit/
│   └── config.toml              # Streamlit 运行时配置
├── .trae/rules/
│   └── commenting_standards.md  # 代码注释规范
├── agents/                      # AI Agent 模块
│   ├── __init__.py
│   ├── auditor_agent.py         # 初级审计员 Agent
│   ├── challenger_agent.py      # 反方审计员 Agent
│   └── senior_partner_agent.py  # 高级合伙人 Agent
├── core/                        # 核心基础设施
│   ├── __init__.py
│   ├── data_loader.py           # 数据加载与异常扫描
│   ├── rag_engine.py            # RAG 检索引擎
│   └── utils.py                 # 跨平台路径工具
├── .gitignore                   # Git 忽略规则
├── app.py                       # Streamlit 主入口
├── requirements.txt             # Python 依赖
└── run_audit.bat                # Windows 启动脚本
```

---

## 系统架构

### 数据流转架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (UI Layer)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  侧边栏: 系统环境 / 语言切换 / AI 模型配置                  │  │
│  │  主界面: 文件上传 / 数据预览 / 扫描结果 / Agent 报告        │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
    │  AuditData-  │  │  RAG Engine  │  │    Agent Pipeline    │
    │   Loader     │  │ (Knowledge   │  │                      │
    │              │  │  Base)       │  │  ┌────────────────┐  │
    │ - load_excel │  │              │  │  │ JuniorAuditor  │  │
    │ - basic_scan │  │ - build_     │  │  │   Agent        │  │
    │              │  │   index      │  │  └───────┬────────┘  │
    │ 检测:        │  │ - retrieve_  │  │          ▼           │
    │  - 负金额    │  │   rules      │  │  ┌────────────────┐  │
    │  - 重复行    │  │              │  │  │  Challenger    │  │
    │              │  │ Embedding:   │  │  │   Agent        │  │
    │ 输出:        │  │ HuggingFace  │  │  └───────┬────────┘  │
    │  anomalies + │  │ Vector:      │  │          ▼           │
    │  stats       │  │ Chroma       │  │  ┌────────────────┐  │
    └──────────────┘  └──────────────┘  │  │ SeniorPartner  │  │
                                        │  │   Agent        │  │
                                        │  └────────────────┘  │
                                        └──────────────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  LLM Backend │
                                        │  (Ollama /   │
                                        │   DeepSeek / │
                                        │   OpenAI)    │
                                        └──────────────┘
```

### 执行时序

1. **用户上传 Excel 文件** → `AuditDataLoader.load_excel()` 加载数据
2. **列名自动适配** → 识别 "Amount/金额/数据/数值" 列并统一重命名为 "Amount"
3. **初步扫描** → `AuditDataLoader.basic_scan()` 检测负金额和重复行
4. **生成 AI 报告** → 三阶段 Agent 串行执行：
   - Phase 1: `JuniorAuditorAgent.generate_report()` → 输出 JSON {analysis, risk_score}
   - Phase 2: `ChallengerAgent.generate_rebuttal()` → 输出 JSON {rebuttal, adjusted_risk_score}
   - Phase 3: `SeniorPartnerAgent.generate_verdict()` → 输出 JSON {final_verdict, final_risk_score, reasoning, action_item}

---

## 模块职责说明

### 1. app.py — 应用入口与 UI 层

**职责**：Streamlit 主界面入口，负责 UI 渲染、状态管理、用户交互编排。

**关键功能**：
- 侧边栏系统环境展示与语言切换器
- AI 引擎配置（模型选择、API Key 输入）
- 文件上传与数据加载
- 异常扫描触发与结果展示
- 三阶段 Agent 串行审计触发与结果渲染

**核心函数**：

| 函数 | 说明 |
|------|------|
| `clear_ai_state()` | 语言切换时清空所有 AI 生成的报告，防止语言不匹配 |
| `reset_all_state()` | 清除所有业务缓存，打破 Streamlit 文件缓存机制 |

**Session State 管理**：

| Key | 类型 | 说明 |
|-----|------|------|
| `lang` | str | 当前界面语言 ("English" / "中文") |
| `df` | DataFrame | 加载的审计数据 |
| `scan_results` | dict | 异常扫描结果 |
| `junior_analysis` | str | 初级审计员分析文本 |
| `junior_score` | int | 初级风险评分 (0-100) |
| `challenger_rebuttal` | str | 反方复核意见 |
| `challenger_score` | int | 反方调整后风险评分 (0-100) |
| `partner_verdict` | str | 最终裁决 ("True Anomaly" / "False Positive") |
| `partner_risk` | int | 合伙人风险评分 (0-100) |
| `partner_reasoning` | str | 最终裁决理由 |
| `partner_action` | str | 下一步行动建议 |
| `model_choice` | str | 选择的模型 ("Local (Ollama)" / "DeepSeek API" / "OpenAI API") |
| `api_key` | str | API 密钥 |
| `api_base` | str | API 接口地址 |

**文本字典 (TEXT)**：
- `TEXT["English"]` — 英文界面文本
- `TEXT["中文"]` — 中文界面文本

**判决映射 (VERDICT_MAP)**：
- 将 JSON 中的英文判决值转换为对应语言的界面显示文本

---

### 2. core/data_loader.py — 数据加载与扫描引擎

**类：AuditDataLoader**

审计数据加载器，封装文件读取和异常扫描逻辑。

| 方法 | 静态 | 输入 | 输出 | 说明 |
|------|------|------|------|------|
| `load_excel(file_obj)` | 是 | 文件对象 (Streamlit UploadedFile) | pd.DataFrame | 读取 Excel 文件，文件为空时抛出 ValueError |
| `basic_scan(df)` | 是 | pd.DataFrame | dict {anomalies, stats} | 执行基础审计扫描 |

**basic_scan 输出结构**：
```python
{
    "anomalies": {
        "Negative Amounts": DataFrame,  # Amount < 0 的记录
        "Duplicate Rows": DataFrame     # 完全重复的行
    },
    "stats": {
        "total_records": int,           # 总记录数
        "anomaly_count": int,           # 异常总数
        "max_amount": float or None     # 最大金额
    }
}
```

---

### 3. core/rag_engine.py — RAG 检索引擎

**类：AuditKnowledgeBase**

审计知识库，封装 PDF 入库和语义向量检索逻辑。

**构造函数参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `knowledge_base_dir` | PathLike | `<project_root>/knowledge_base` | PDF 知识库目录 |
| `persist_dir` | PathLike | `<project_root>/chroma_db` | Chroma 持久化目录 |
| `embedding_model` | str | `"shibing624/text2vec-base-chinese"` | HuggingFace 词向量模型 |
| `chunk_size` | int | 800 | 文本切块长度 |
| `chunk_overlap` | int | 120 | 相邻切块重叠长度 |

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `build_index(pdf_path)` | PDF 文件/目录路径 | int (写入块数) | 读取 PDF、切块、写入 Chroma 向量库 |
| `retrieve_rules(query, top_k=2)` | 查询字符串, 返回数量 | List[str] | 语义检索最相关的准则文本 |
| `_collect_pdf_files(pdf_path)` | 路径 | List[Path] | 收集指定路径下的 PDF 文件 |
| `_resolve_pdf_input(pdf_path)` | 路径 | Path | 解析 PDF 输入路径（相对路径优先解析到 knowledge_base） |
| `_resolve_path(path, base_dir)` | 路径, 基准目录 | Path | [Cross-Platform] 跨平台路径解析 |
| `_iter_pdf_files(directory)` | 目录 | Iterable[Path] | 递归遍历目录中的 PDF 文件 |

**依赖的外部库**：
- `langchain_community.document_loaders.PyPDFLoader` — PDF 文档加载
- `langchain_text_splitters.RecursiveCharacterTextSplitter` — 文本切分
- `langchain_huggingface.HuggingFaceEmbeddings` — 词向量嵌入
- `langchain_chroma.Chroma` — 向量数据库

---

### 4. core/utils.py — 跨平台路径工具

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `get_project_root()` | 无 | Path | 动态解析项目根目录（基于当前文件位置） |
| `get_mock_data_path()` | 无 | Path | 获取 mock_data 目录路径 |

**跨平台设计**：统一使用 pathlib，通过 `/` 运算符自动适配不同操作系统的路径分隔符。

---

### 5. agents/auditor_agent.py — 初级审计员 Agent

**类：JuniorAuditorAgent**

初级审计 Agent，将异常数据交由 LLM 生成初步审计意见。

**构造函数参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `lang` | str | "English" | 输出语言 ("English" / "中文") |
| `api_key` | str | "" | API 密钥 |
| `api_base` | str | "" | API 接口地址 |

**模型路由逻辑**：
- 当 `api_base` 包含 "localhost" 时 → 使用 `"llama3:8b"`（本地 Ollama）
- 否则 → 使用 `"gpt-4o-mini"`（云端 OpenAI/DeepSeek）

| 方法 | 静态 | 输入 | 输出 | 说明 |
|------|------|------|------|------|
| `__init__()` | 否 | lang, api_key, api_base | 实例 | 初始化 OpenAI 客户端，校验 API Key |
| `_format_anomalies(anomalies_dict)` | 是 | 异常字典 | str | 将 DataFrame 异常字典格式化为纯文本 |
| `generate_report(anomalies_dict, stats)` | 否 | 异常字典, 统计指标 | str (JSON) | 向 LLM 发送请求，返回 JSON 格式的审计报告 |

**输出 JSON 结构**：
```json
{
    "analysis": "审计分析文本",
    "risk_score": 75
}
```

**API 调用参数**：
- `temperature`: 0.3
- `max_tokens`: 1024
- `response_format`: `{"type": "json_object"}`

---

### 6. agents/challenger_agent.py — 反方审计员 Agent

**类：ChallengerAgent**

反方审计 Agent，独立评估异常数据，对初级审计员的结论进行复核与质疑。

**构造函数参数**：同 JuniorAuditorAgent

| 方法 | 静态 | 输入 | 输出 | 说明 |
|------|------|------|------|------|
| `__init__()` | 否 | lang, api_key, api_base | 实例 | 初始化 OpenAI 客户端 |
| `_format_anomalies(anomalies_dict)` | 是 | 异常字典 | str | 格式化异常数据为纯文本 |
| `generate_rebuttal(anomalies_dict, stats, junior_report, junior_score)` | 否 | 异常字典, 统计指标, 初级报告, 初级评分 | str (JSON) | 生成独立反驳意见 |

**输出 JSON 结构**：
```json
{
    "rebuttal": "反驳分析文本",
    "adjusted_risk_score": 30
}
```

**API 调用参数**：
- `temperature`: 0.4（略高于 Junior，鼓励更多独立观点）
- `max_tokens`: 1024
- `response_format`: `{"type": "json_object"}`

---

### 7. agents/senior_partner_agent.py — 高级合伙人 Agent

**类：SeniorPartnerAgent**

高级合伙人 Agent，综合两方报告做出最终仲裁裁决。

**构造函数参数**：同 JuniorAuditorAgent

| 方法 | 静态 | 输入 | 输出 | 说明 |
|------|------|------|------|------|
| `__init__()` | 否 | lang, api_key, api_base | 实例 | 初始化 OpenAI 客户端 |
| `generate_verdict(total_records, anomaly_count, junior_report, junior_score, challenger_rebuttal, challenger_score)` | 否 | 案件摘要, 两方报告与评分 | str (JSON) | 做出最终裁决 |

**输出 JSON 结构**：
```json
{
    "final_verdict": "True Anomaly" 或 "False Positive",
    "final_risk_score": 75,
    "reasoning": "裁决理由",
    "action_item": "下一步行动建议"
}
```

**API 调用参数**：
- `temperature`: 0.3
- `max_tokens`: 1024
- `response_format`: `{"type": "json_object"}`

---

## 依赖关系

### 核心依赖链

```
app.py
├── core/utils.py
├── core/data_loader.py ──→ pandas, openpyxl
├── agents/auditor_agent.py ──→ openai
├── agents/challenger_agent.py ──→ openai
└── agents/senior_partner_agent.py ──→ openai

core/rag_engine.py
├── langchain_community (PyPDFLoader)
├── langchain_text_splitters (RecursiveCharacterTextSplitter)
├── langchain_huggingface (HuggingFaceEmbeddings)
└── langchain_chroma (Chroma)
```

### Python 依赖清单 (requirements.txt)

| 包名 | 最低版本 | 用途 |
|------|----------|------|
| streamlit | >=1.28.0 | Web UI 框架 |
| pandas | >=2.0.0 | 数据处理与分析 |
| openpyxl | >=3.1.0 | Excel 文件读取引擎 |
| openai | >=1.0.0 | 兼容 OpenAI 标准的 LLM 客户端 |
| python-dotenv | >=1.0.0 | 环境变量加载 |
| langchain-community | >=0.3.0 | LangChain 社区组件（PDF 加载器等） |
| langchain-text-splitters | >=0.3.0 | 文档文本切分工具 |
| langchain-huggingface | >=0.1.0 | HuggingFace 词向量集成 |
| langchain-chroma | >=0.1.4 | Chroma 向量数据库集成 |
| chromadb | >=0.5.0 | 本地向量数据库 |
| pypdf | >=4.0.0 | PDF 解析 |
| sentence-transformers | >=3.0.0 | 句子向量模型 |

---

## 项目运行方式

### 环境准备

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

2. **激活虚拟环境**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

### 启动应用

#### 方式一：直接命令行启动
```bash
python -m streamlit run app.py
```

#### 方式二：Windows 批处理脚本
```bash
run_audit.bat
```
> 注意：此脚本假设虚拟环境位于项目根目录下的 `venv` 文件夹。

### 模型配置

启动后在侧边栏选择 AI 模型：

| 模型选项 | API Base | API Key | 说明 |
|----------|----------|---------|------|
| Local (Ollama) | `http://localhost:11434/v1` | 占位符 `ollama_local` | 100% 本地私有，数据不离开设备 |
| DeepSeek API | `https://api.deepseek.com/v1` | 用户自行填写 | 云端模型，财务数据会发送至外部服务器 |
| OpenAI API | `https://api.openai.com/v1` | 用户自行填写 | 云端模型，财务数据会发送至外部服务器 |

**Ollama 本地部署要求**：
- 需提前安装 Ollama 并拉取 `llama3:8b` 模型
- 确保 Ollama 服务正在运行 (`ollama serve`)

### 使用流程

1. 选择界面语言 (English / 中文)
2. 配置 AI 模型（选择模型并填写 API Key，如需）
3. 上传 Excel 审计文件 (.xlsx)
4. 查看数据预览
5. 点击 "运行初步扫描" 查看异常检测结果
6. 点击 "生成 AI 报告" 触发三阶段 Agent 串行审计
7. 查看 Junior Auditor / Challenger / Senior Partner 的审计意见与裁决

---

## 关键设计决策

### 1. 状态管理策略

- 使用 Streamlit `session_state` 管理所有运行时状态
- 语言切换时通过 `on_change=clear_ai_state` 清空 AI 报告，防止多语言内容混合
- 文件变更时通过 `on_change=reset_all_state` 清除所有缓存，确保数据新鲜度

### 2. JSON 容错处理

所有 Agent 的 LLM 输出均包裹 JSON 解析防护：
- 尝试 `json.loads()` 解析
- 捕获 `JSONDecodeError` / `TypeError` / `ValueError`
- 解析失败时回退到原始输出，并在 UI 中显示错误提示

### 3. 列名自适应

数据加载后自动识别并统一金额列名：
- 候选列名: `["data", "Amount", "金额", "数值"]`
- 匹配后统一重命名为 `"Amount"`，确保后续 `basic_scan` 正常工作

### 4. 跨平台路径处理

- 所有路径操作使用 `pathlib.Path`
- 通过 `/` 运算符拼接路径，自动适配操作系统分隔符
- 项目根目录通过 `Path(__file__).resolve().parent.parent` 动态解析

### 5. 风险等级判定

- Challenger 调整后分数 > 60 → **高风险** (建议人工立即介入)
- 否则 → **低风险** (大概率为正常业务冲销)

---

## 扩展说明

### RAG 知识库集成

`AuditKnowledgeBase` 类为独立模块，当前未在 `app.py` 主流程中调用，但已具备完整功能：
- `build_index()` 可将 PDF 审计准则切块并索引到 Chroma 向量库
- `retrieve_rules()` 可根据查询语义检索最相关的准则片段
- 使用 HuggingFace 中文词向量模型 `shibing624/text2vec-base-chinese`

如需在 Agent Prompt 中引入 RAG 上下文，可在 `generate_report()` 等方法中调用 `retrieve_rules()` 获取相关准则并注入 Prompt。

### .gitignore 覆盖范围

项目 .gitignore 已覆盖：
- 操作系统特有文件（.DS_Store, Thumbs.db 等）
- Python 运行时（.env, __pycache__, venv 等）
- IDE 配置（.idea/, .vscode/）
- C/C++ 编译产物（预留 engine_cpp 目录支持）
