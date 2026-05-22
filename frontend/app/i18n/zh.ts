export const zh = {
  nav: {
    console: "控制台",
    arena: "虚拟审计组",
    papers: "审计工作底稿"
  },
  layout: {
    title: "Enterprise Penetration Audit System", // keeps branding
    subtitle: "企业穿透式审计系统",
    version: "v1.0.0"
  },
  console: {
    title: "审计控制台",
    subtitle: "上传审计数据完成规则穿透扫描，并进入虚拟审计组查看多 Agent 质证与仲裁链路。",
    arenaBtn: "虚拟审计组",
    metrics: {
      consistency: "一致性",
      scanned: "扫描数",
      anomalies: "异常数",
      exposure: "暴露金额",
      records: "条记录"
    },
    verdict: {
      passed: "审计通过 — 所有检查已清除",
      failed: "评分 {score} 低于阈值",
      regressed: "已回退至审核阶段 · 阈值 {threshold}"
    },
    upload: {
      analyzing: "正在分析...",
      uploadXlsx: "上传 .xlsx 审计文件",
      offlineTip: "后端连接恢复后即可上传",
      dragTip: "拖拽文件到此处，或点击选择文件",
      formatError: "请上传 .xlsx 格式的审计数据文件。",
      backendError: "后端服务未连接。请确认 AuditCore API 已在 {url} 启动。",
      genericError: "上传失败，请检查文件内容或后端服务状态。"
    },
    api: {
      connected: "后端已连接",
      checking: "正在检查后端连接",
      disconnected: "后端未连接",
      recheck: "重新检查"
    },
    table: {
      findings: "发现规则 ({count})",
      rule: "规则",
      records: "记录数",
      summary: "发现摘要",
      severity: "严重程度",
      high: "高",
      low: "低"
    }
  },
  papers: {
    back: "返回控制台",
    title: "审计工作底稿",
    subtitle: "基于最近一次上传文件自动生成底稿摘要，包含扫描概览、规则发现、证据节点和下一步审计动作。",
    uploadedAt: "上传时间：{time}",
    refresh: "刷新",
    copyPaper: "复制底稿",
    copied: "已复制",
    copyFailed: "复制失败",
    downloadMd: "下载 Markdown",
    metrics: {
      scanned: "总记录数",
      anomalies: "异常记录",
      exposure: "最大金额",
      riskLevel: "风险等级"
    },
    findings: {
      title: "规则发现",
      desc: "来自当前上传文件的实时规则扫描结果。",
      items: "{count} 条"
    },
    evidence: {
      title: "证据节点",
      desc: "底稿中保留的规则事实节点，后续可连接多 Agent 质证关系。",
      empty: "当前扫描没有生成证据节点。"
    },
    preview: {
      title: "Markdown 底稿预览",
      desc: "可直接复制或下载，用作专利演示和审计归档材料。"
    },
    empty: {
      title: "请先上传审计文件",
      desc: "工作底稿页会读取最近一次 Excel 上传结果，并自动生成可复制、可下载的 Markdown 底稿。",
      btn: "返回上传"
    },
    error: {
      title: "无法连接后端",
      desc: "请确认 AuditCore API 已在 {url} 启动，然后重新加载底稿。",
      btn: "重新加载"
    },
    loading: {
      title: "正在读取最新审计结果",
      desc: "系统正在从后端获取最近一次上传文件的扫描结果。"
    },
    risk: {
      high: "高风险",
      medium: "中风险",
      low: "低风险",
      unidentified: "未识别"
    },
    doc: {
      title: "审计工作底稿",
      section1: "1. 审计对象",
      fileName: "文件名称",
      uploadedAt: "上传时间",
      source: "数据来源",
      sourceVal: "AuditCore Excel 上传审计",
      section2: "2. 扫描概览",
      scanned: "总记录数",
      anomalies: "异常记录数",
      exposure: "最大金额",
      consistency: "全局一致性评分",
      riskLevel: "风险等级",
      section3: "3. 规则发现",
      emptyFindings: "未生成规则发现。",
      section4: "4. 证据节点",
      emptyEvidence: "当前无异常证据节点。",
      section5: "5. 审计结论",
      conclusionPositive: "本次规则扫描发现异常记录，建议进入多 Agent 复核和凭证补证流程。",
      conclusionNegative: "本次规则扫描未发现异常记录，建议按常规流程归档，并保留抽样记录。",
      section6: "6. 下一步动作",
      actionPositive: "- 调取原始凭证、审批流和业务说明。\n- 将异常规则发现提交虚拟审计组进行质证和仲裁。\n- 对高金额或重复记录形成专项底稿附件。",
      actionNegative: "- 保存本次扫描记录。\n- 确认数据覆盖期间和字段映射完整性。\n- 按常规审计归档流程处理。"
    }
  },
  arena: {
    back: "返回控制台",
    title: "多 Agent 协作虚拟审计组",
    subtitleLabel: "多 Agent 协作虚拟审计组",
    fileName: "数据来源：{file} · 上传时间 {time}",
    metrics: {
      anomalies: "异常记录",
      exposure: "风险暴露",
      consistency: "一致性",
      caseId: "案例编号"
    },
    division: {
      title: "审计组分工",
      desc: "四类 Agent 按审计职责拆分观点、质疑、核验和裁决。"
    },
    timeline: {
      title: "协作时间线",
      desc: "从制度检索到最终仲裁，保留每一步可解释的决策轨迹。"
    },
    relations: {
      title: "证据支持与冲突关系",
      desc: "用轻量证据图表达事实节点如何影响最终裁决。"
    },
    output: {
      title: "当前 Agent 输出",
      empty: "暂无输出。"
    },
    decision: {
      title: "最终仲裁",
      verdict: "裁决",
      riskLevel: "风险等级",
      finalScore: "最终风险分",
      status: "输出状态",
      archived: "已归档",
      basis: "仲裁依据",
      nextAction: "下一步审计动作"
    },
    loop: {
      title: "技术闭环状态",
      rag: "RAG 路径优化",
      ragStatus: "制度依据已检索",
      hallucination: "防幻觉核查",
      hallucinationStatus: "证据支持度 {score}",
      decision: "多 Agent 决策",
      decisionStatus: "仲裁结论已形成",
      privacy: "隐私脱敏"
    },
    empty: {
      title: "请先上传审计文件",
      desc: "虚拟审计组现在读取最近一次 Excel 上传结果，并基于真实规则扫描结果生成多 Agent 分析。",
      btn: "上传 .xlsx 文件"
    },
    agentRoles: {
      junior: {
        title: "初级审计 Agent",
        responsibility: "汇总规则扫描事实，形成初步审计判断。",
        scoreLabel: "初始风险"
      },
      challenger: {
        title: "反方复核 Agent",
        responsibility: "独立质疑初审结论，识别过度判断或遗漏证据。",
        scoreLabel: "调整风险"
      },
      factCheck: {
        title: "事实核查 Agent",
        responsibility: "将结论映射回原始证据，计算支持度与冲突度。",
        scoreLabel: "支持 / 冲突"
      },
      partner: {
        title: "高级合伙人 Agent",
        responsibility: "综合多方观点，输出最终裁决和下一步审计动作。",
        scoreLabel: "最终风险"
      }
    },
    agentStatus: {
      completed: "已完成",
      arbitrating: "仲裁中",
      archived: "已归档"
    },
    relationsLabel: {
      support: "支持",
      conflict: "冲突",
      security: "安全"
    },
    timelineData: [
      {
        stage: "01",
        title: "RAG 检索定位制度依据",
        description: "检索付款审批、供应商管理和发票归档规则，为后续判断建立依据边界。",
        owner: "规则与知识库"
      },
      {
        stage: "02",
        title: "初审形成风险假设",
        description: "初级审计 Agent 将异常流水转化为可质证的初步结论和风险评分。",
        owner: "初级审计 Agent"
      },
      {
        stage: "03",
        title: "反方复核触发博弈",
        description: "反方复核 Agent 专门寻找反例、遗漏字段和替代解释，防止单一路径误判。",
        owner: "反方复核 Agent"
      },
      {
        stage: "04",
        title: "事实核查生成证据关系",
        description: "Fact-checking Agent 把观点绑定到证据节点，标记支持边与冲突边。",
        owner: "事实核查 Agent"
      },
      {
        stage: "05",
        title: "合伙人仲裁输出动作",
        description: "高级合伙人 Agent 根据支持度、冲突度和风险暴露给出最终审计动作。",
        owner: "高级合伙人 Agent"
      }
    ],
    dynamic: {
      risk: {
        high: "高风险",
        medium: "中风险",
        low: "低风险"
      },
      uploadedAudit: "上传文件实时审计",
      unknownTime: "未知时间",
      noFindings: "未发现有效异常规则命中",
      hasAnomaliesTitle: "规则复核",
      noAnomaliesTitle: "上传数据未触发异常规则",
      sourceSummaryAnomalies: "基于你上传的 {file}，系统扫描 {total} 条记录，发现 {anomaly} 条异常，主要命中 {finding}。",
      sourceSummaryNoAnomalies: "基于你上传的 {file}，系统扫描 {total} 条记录，当前未发现规则层异常。",
      ruleHit: "{label} 命中 {count} 条记录，支持继续审计追查。",
      ruleNotHit: "{label} 未命中，降低该类异常的确定性。",
      scanStatsContent: "总记录 {total} 条，异常 {anomaly} 条，最高金额 {max}。",
      scanStatsMaxUnidentified: "未识别",
      privacyGuardContent: "虚拟审计组只读取规则摘要、统计值和证据节点，不展示原始敏感字段明细。",
      evidenceEdgeScanStatsRationaleSupport: "异常数量和金额暴露形成整体风险背景。",
      evidenceEdgeScanStatsRationaleConflict: "当前扫描统计未形成明显异常压力。",
      evidenceEdgePrivacyGuardRationale: "协作展示不暴露原始敏感字段，满足安全闭环要求。",
      juniorSummaryAnomalies: "发现 {anomaly} 条异常，建议进入复核程序。",
      juniorSummaryNoAnomalies: "规则扫描未发现异常，建议归档并保留抽样记录。",
      juniorAnalysisAnomalies: "上传文件共 {total} 条记录，规则层发现 {finding}。初审认为该批数据存在可审计异常，需要进入多 Agent 复核。",
      juniorAnalysisNoAnomalies: "上传文件共 {total} 条记录，当前规则扫描未命中异常，初审倾向于低风险归档。",
      challengerSummaryAnomalies: "风险信号成立，但规则扫描仍需结合业务凭证确认。",
      challengerSummaryNoAnomalies: "未见规则异常，但仍建议确认字段映射和样本完整性。",
      challengerRebuttalAnomalies: "反方认为 {finding} 只能证明规则命中，尚不能直接证明舞弊或错误入账；需补充原始凭证、审批流和业务背景。",
      challengerRebuttalNoAnomalies: "反方未发现可推翻低风险判断的证据，但提醒应确认上传文件是否覆盖完整审计期间。",
      factCheckSummaryAnomalies: "规则事实支持异常判断，冲突主要来自业务解释尚未补齐。",
      factCheckSummaryNoAnomalies: "事实层未形成异常支持，冲突点集中在数据完整性确认。",
      factCheckAnalysisAnomalies: "事实核查将 {count} 类异常规则映射为证据节点。支持度来自规则命中和金额暴露，冲突度来自缺少凭证级解释。",
      factCheckAnalysisNoAnomalies: "事实核查未找到规则命中节点，支持低风险结论；仍需确认字段命名、金额列和重复行规则是否适用于本数据。",
      partnerSummaryAnomalies: "维持异常判断，进入专项底稿和凭证补证。",
      partnerSummaryNoAnomalies: "暂不认定异常，建议归档并保留抽样复核记录。",
      partnerReasoningAnomalies: "规则命中、异常数量和金额暴露共同支持继续审计；反方意见降低确定性，但不足以推翻异常方向。",
      partnerReasoningNoAnomalies: "规则扫描未形成足够支持证据，当前更适合低风险归档或扩大样本后再评估。",
      partnerActionAnomalies: "生成专项审计底稿，调取原始凭证、审批流和业务说明。",
      partnerActionNoAnomalies: "记录本次扫描结果，确认数据覆盖范围后进入常规归档。",
      finalDecisionReasoningAnomalies: "多 Agent 根据你上传文件的规则命中结果完成仲裁：{finding}，最终风险分 {score}/100。",
      finalDecisionReasoningNoAnomalies: "多 Agent 根据你上传文件的扫描结果完成仲裁：当前异常证据不足，最终风险分 {score}/100。",
      finalDecisionActionAnomalies: "生成专项审计底稿，并向业务/财务团队发起凭证补证请求。",
      finalDecisionActionNoAnomalies: "保留审计扫描记录，按常规流程归档。"
    }
  }
};
