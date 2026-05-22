# Tasks

- [ ] Task 1: 创建底稿生成Agent（WorkingPaperAgent）
  - [ ] Task 1.1: 在 agents/ 目录下创建 working_paper_agent.py，实现结构化审计工作底稿生成逻辑
  - [ ] Task 1.2: 在 agents/__init__.py 中导出 WorkingPaperAgent
  - [ ] Task 1.3: 在 core/contracts.py 中新增底稿相关数据结构（WorkingPaperSection 等）

- [ ] Task 2: 实现DAG状态机调度模块
  - [ ] Task 2.1: 在 core/ 目录下创建 dag_scheduler.py，实现DAG状态图数据结构
  - [ ] Task 2.2: 定义节点类型枚举（INIT、RULE_SCAN、FACT_CHECK、WORKING_PAPER、FINAL_VERDICT、ROLLBACK_REVIEW）
  - [ ] Task 2.3: 实现状态转移条件评估（基于优先级与置信度）
  - [ ] Task 2.4: 实现Agent调用顺序管理（拓扑排序+动态优先级）

- [ ] Task 3: 实现动态流程控制模块
  - [ ] Task 3.1: 在 core/ 目录下创建 flow_controller.py
  - [ ] Task 3.2: 实现局部子图一致性评分计算（subgraph-level consistency scoring）
  - [ ] Task 3.3: 实现冲突检测与回退触发逻辑
  - [ ] Task 3.4: 实现局部回滚机制（仅涉及冲突子图的Agent任务回滚）

- [ ] Task 4: 增强现有EvidenceGraph模块
  - [ ] Task 4.1: 在 evidence_graph.py 中新增局部子图提取方法 get_subgraph()
  - [ ] Task 4.2: 在 evidence_graph.py 中新增子图一致性评分计算方法 calculate_subgraph_consistency()
  - [ ] Task 4.3: 在 evidence_graph.py 中新增冲突边查询方法 get_conflict_edges()

- [ ] Task 5: 增强后端API以支持多Agent流水线
  - [ ] Task 5.1: 在 server.py 中新增 /api/audit/multi-agent 端点
  - [ ] Task 5.2: 实现完整的多Agent流水线执行逻辑（规则扫描 → 事实核查 → 底稿生成）
  - [ ] Task 5.3: 返回增强的审计结果数据结构（包含Agent集群状态、证据图、DAG轨迹、底稿）
  - [ ] Task 5.4: 实现Agent执行进度SSE推送（可选，用于前端实时展示）

- [ ] Task 6: 开发Agent Arena前端可视化页面
  - [ ] Task 6.1: 重新设计 frontend/app/arena/page.tsx，从占位页升级为完整可视化界面
  - [ ] Task 6.2: 实现证据图可视化组件（节点、边、评分展示）
  - [ ] Task 6.3: 实现DAG状态机可视化组件（状态节点、转移路径、当前状态高亮）
  - [ ] Task 6.4: 实现多Agent集群状态面板（各Agent工作进度、输出摘要）
  - [ ] Task 6.5: 实现冲突仲裁与底稿输出展示区域
  - [ ] Task 6.6: 实现前端与后端API的数据联动（文件上传触发多Agent流水线）

- [ ] Task 7: 前端布局与导航增强
  - [ ] Task 7.1: 在 layout.tsx 中修正Agent Arena导航激活状态判断逻辑
  - [ ] Task 7.2: 确保首页与Arena页之间的数据联动（上传文件可在Arena页查看全流程）

- [ ] Task 8: 端到端测试与验证
  - [ ] Task 8.1: 使用 complex_audit_test.xlsx 测试完整的多Agent流水线
  - [ ] Task 8.2: 验证前端可视化各组件数据展示正确性
  - [ ] Task 8.3: 验证一致性评分、状态转移、冲突回滚逻辑

# Task Dependencies

- Task 1 依赖 Task 4（底稿生成需要增强的证据图）
- Task 2 依赖 Task 4（DAG状态机需要增强的证据图模块）
- Task 3 依赖 Task 2（流程控制依赖DAG状态机）
- Task 5 依赖 Task 1、Task 2、Task 3（API需要所有后端模块就绪）
- Task 6 依赖 Task 5（前端需要后端API支持）
- Task 7 依赖 Task 6（布局增强在Arena页面完成后进行）
- Task 8 依赖 Task 5、Task 6、Task 7（端到端测试需要前后端全部就绪）
