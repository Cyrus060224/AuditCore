# 多Agent协作虚拟审计组 Spec

## Why
现有审计流程存在人工效率低、多文档幻觉、证据不一致、隐私泄露风险等核心痛点。本专利方向旨在通过多智能体协同与证据一致性约束机制，完整模拟"虚拟审计组"全流程，实现审计工作流的自动化与可追溯。

## What Changes
- 新增底稿生成Agent（WorkingPaperAgent），与现有RuleAgent、FactCheckAgent形成三类Agent集群
- 新增DAG状态机调度模块，实现状态转移控制与Agent调用顺序管理
- 新增动态流程控制模块，基于一致性评分驱动的冲突消解与局部回滚
- 前端新增Agent Arena页面，可视化展示多Agent协作全流程、证据图博弈轨迹、仲裁结论
- 后端API增强：支持完整的多Agent审计流水线执行与结果返回
- 新增审计工作底稿结构化输出模块

## Impact
- **后端变更**: `server.py` (扩展审计API), `agents/` (新增底稿Agent), `core/` (DAG状态机、流程控制)
- **前端变更**: `frontend/app/arena/page.tsx` (从占位页升级为完整可视化), `frontend/app/page.tsx` (可能调整)
- **影响范围**: 核心审计流水线、前端展示层、API接口

## ADDED Requirements

### Requirement: 多Agent集群架构
系统应提供由三类Agent组成的任务专精集群：
- 规则穿透Agent（RuleAgent）：负责传统硬性规则引擎+SQL表格推理，实现财务数据穿透测试
- 事实核查Agent（FactCheckAgent）：负责证据溯源与Fact-checking，消除幻觉
- 底稿生成Agent（WorkingPaperAgent）：负责结构化审计工作底稿的自动生成与格式化

#### Scenario: Agent集群初始化
- **WHEN** 用户上传审计数据文件
- **THEN** 系统按依赖顺序初始化三类Agent集群，各Agent包含处理单元及对应的任务执行规则

### Requirement: 证据图构建与一致性评分
系统应构建审计证据图G（节点为原子事实，边为支持/冲突关系），并计算全局一致性评分。

#### Scenario: 一致性评分计算
- **WHEN** 规则穿透Agent产出规则发现
- **THEN** 系统构建证据图节点和边，执行一致性评分公式计算全局一致性评分

### Requirement: DAG状态机驱动的工作流
整个流程由有向无环状态机（DAG状态图）驱动，状态机以结构化工作流定义文件描述，包括节点类型、状态转移条件及任务依赖关系。

#### Scenario: 状态转移控制
- **WHEN** 一致性评分低于预设阈值
- **THEN** 自动触发回退至上游状态机节点，重新调度冲突相关Agent并执行冲突消解
- **WHEN** 一致性评分达到阈值
- **THEN** 进入下一任务节点，直至底稿生成Agent输出结构化审计工作底稿

### Requirement: 动态流程控制与冲突消解
当全局或任一局部子图Gi的一致性评分低于预设阈值时，基于一致性评分驱动的动态流程控制机制自动触发回退，执行冲突消解（fact-level contradiction detection + 加权投票）。

#### Scenario: 局部回滚机制
- **WHEN** 局部子图Gi的一致性评分低于全局评分阈值
- **THEN** 优先回滚仅涉及Gi的Agent任务，而非全局重启

### Requirement: Agent Arena前端可视化
前端应提供完整的Agent协作流程可视化页面，展示：
- 多Agent集群状态与实时协作过程
- 证据图结构可视化（节点、边、一致性评分）
- DAG状态机当前状态与历史轨迹
- 冲突仲裁结果与底稿输出

#### Scenario: 可视化审计全流程
- **WHEN** 用户进入Agent Arena页面并上传数据
- **THEN** 实时展示各Agent工作进度、证据图演化、评分变化、状态转移

### Requirement: 审计工作底稿生成
系统应自动生成结构化审计工作底稿，包含审计概览、事实清单、图谱博弈轨迹、仲裁结论等章节。

#### Scenario: 底稿导出
- **WHEN** 审计流程完成且一致性评分达标
- **THEN** 输出结构化审计工作底稿（Markdown格式），包含显式溯源链接

## MODIFIED Requirements

### Requirement: RuleAgent规则扫描
现有RuleAgent需增强以支持多Agent流水线集成，输出标准化RuleFinding对象供证据图构建。

### Requirement: FactCheckAgent事实核查
现有FactCheckAgent需增强以支持二部图映射的事实单元溯源及校验，纳入动态流程控制体系。

### Requirement: EvidenceGraph证据图
现有EvidenceGraph需增强以支持局部子图一致性评分计算，支持冲突边权重动态更新。

### Requirement: 前端布局
现有前端布局需新增Agent Arena为一级导航项，并增强首页与Arena页的数据联动。

## REMOVED Requirements

无删除需求。
