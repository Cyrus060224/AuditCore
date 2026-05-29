export const en = {
  nav: {
    console: "Console",
    arena: "Agent Arena",
    papers: "Working Papers",
    settings: "Model Config"
  },
  layout: {
    title: "AuditCore",
    subtitle: "Enterprise Penetration Audit System",
    version: "v1.0.0"
  },
  console: {
    title: "Audit Console",
    subtitle: "Upload audit data to complete rule penetration scanning, and enter the virtual audit group to view the multi-agent testimony and arbitration chain.",
    arenaBtn: "Agent Arena",
    metrics: {
      consistency: "Consistency",
      scanned: "Scanned",
      anomalies: "Anomalies",
      exposure: "Exposure",
      records: "records"
    },
    verdict: {
      passed: "Audit passed — all checks cleared",
      failed: "Score {score} below threshold",
      regressed: "Regressed to review stage · threshold {threshold}"
    },
    upload: {
      analyzing: "Analyzing...",
      uploadXlsx: "Upload .xlsx Audit File",
      offlineTip: "Upload will be available once backend connection is restored",
      dragTip: "Drag & drop file here, or click to select",
      formatError: "Please upload audit data in .xlsx format.",
      backendError: "Backend service not connected. Please confirm AuditCore API is started at {url}.",
      genericError: "Upload failed, please check file contents or backend service status."
    },
    api: {
      connected: "Backend Connected",
      checking: "Checking backend connection...",
      disconnected: "Backend Not Connected",
      recheck: "Re-check"
    },
    table: {
      findings: "Findings ({count})",
      rule: "Rule",
      records: "Records",
      summary: "Summary",
      severity: "Severity",
      high: "High",
      low: "Low"
    }
  },
  papers: {
    back: "Back to Console",
    title: "Audit Working Papers",
    subtitle: "Automatically generate working paper summary based on the latest uploaded file, including scan overview, rule findings, evidence nodes, and next audit steps.",
    uploadedAt: "Uploaded At: {time}",
    refresh: "Refresh",
    copyPaper: "Copy Paper",
    copied: "Copied",
    copyFailed: "Copy Failed",
    downloadMd: "Download Markdown",
    metrics: {
      scanned: "Total Records",
      anomalies: "Anomalies",
      exposure: "Max Amount",
      riskLevel: "Risk Level"
    },
    findings: {
      title: "Rule Findings",
      desc: "Real-time rule scanning results from the currently uploaded file.",
      items: "{count} records"
    },
    evidence: {
      title: "Evidence Nodes",
      desc: "Rule fact nodes preserved in the working paper, which can be connected to multi-agent testimony later.",
      empty: "No evidence nodes generated in current scan."
    },
    preview: {
      title: "Markdown Paper Preview",
      desc: "Can be directly copied or downloaded for patent demonstrations and audit archiving."
    },
    empty: {
      title: "Please Upload Audit File First",
      desc: "The working papers page will read the latest Excel upload results and automatically generate copyable and downloadable Markdown papers.",
      btn: "Back to Upload"
    },
    error: {
      title: "Cannot Connect to Backend",
      desc: "Please confirm AuditCore API is started at {url}, then reload the working paper.",
      btn: "Reload"
    },
    loading: {
      title: "Reading Latest Audit Results",
      desc: "The system is fetching scan results of the latest uploaded file from the backend."
    },
    risk: {
      high: "High Risk",
      medium: "Medium Risk",
      low: "Low Risk",
      unidentified: "Unidentified"
    },
    unknownTime: "Unknown Time",
    doc: {
      title: "Audit Working Papers",
      section1: "1. Audit Object",
      fileName: "File Name",
      uploadedAt: "Uploaded At",
      source: "Data Source",
      sourceVal: "AuditCore Excel Upload Audit",
      section2: "2. Scan Overview",
      scanned: "Total Records",
      anomalies: "Anomalies",
      exposure: "Max Amount",
      consistency: "Global Consistency Score",
      riskLevel: "Risk Level",
      section3: "3. Rule Findings",
      emptyFindings: "No rule findings generated.",
      section4: "4. Evidence Nodes",
      emptyEvidence: "No evidence nodes in current scan.",
      section5: "5. Audit Conclusion",
      conclusionPositive: "Abnormal records found in this rule scan. Multi-agent review and voucher supplement process recommended.",
      conclusionNegative: "No abnormal records found in this rule scan. Standard archiving with sample records retention recommended.",
      section6: "6. Next Actions",
      actionPositive: "- Retrieve original credentials, approval flows, and business descriptions.\n- Submit abnormal rule findings to the virtual audit group for testimony and arbitration.\n- Form special working paper attachments for high amounts or duplicate records.",
      actionNegative: "- Save this scan record.\n- Confirm data coverage period and field mapping integrity.\n- Process according to standard audit archiving workflow."
    }
  },
  arena: {
    back: "Back to Console",
    title: "Multi-Agent Collaborative Virtual Audit Group",
    subtitleLabel: "Multi-Agent Collaborative Virtual Audit Group",
    fileName: "Data Source: {file} · Uploaded At {time}",
    metrics: {
      anomalies: "Anomalies",
      exposure: "Risk Exposure",
      consistency: "Consistency",
      caseId: "Case ID"
    },
    division: {
      title: "Audit Group Division",
      desc: "Four categories of agents split views, questioning, verification, and arbitration by audit responsibility."
    },
    timeline: {
      title: "Collaboration Timeline",
      desc: "From system retrieval to final arbitration, preserving an explainable decision path for each step."
    },
    relations: {
      title: "Evidence Support & Conflict Relations",
      desc: "Use a lightweight evidence graph to represent how fact nodes impact the final decision."
    },
    output: {
      title: "Current Agent Output",
      empty: "No output available."
    },
    decision: {
      title: "Final Decision",
      verdict: "Verdict",
      riskLevel: "Risk Level",
      finalScore: "Final Risk Score",
      status: "Output Status",
      archived: "Archived",
      basis: "Arbitration Basis",
      nextAction: "Next Audit Actions"
    },
    loop: {
      title: "Technical Closed-Loop Status",
      rag: "RAG Path Optimization",
      ragStatus: "Regulatory basis retrieved",
      hallucination: "Anti-Hallucination Verification",
      hallucinationStatus: "Evidence support {score}",
      decision: "Multi-Agent Decision",
      decisionStatus: "Arbitration conclusion formed",
      privacy: "Privacy Anonymization"
    },
    empty: {
      title: "Please Upload Audit File First",
      desc: "The virtual audit group now reads the latest Excel upload results and generates multi-agent analyses based on actual rule scan results.",
      btn: "Upload .xlsx File"
    },
    agentRoles: {
      junior: {
        title: "Junior Audit Agent",
        responsibility: "Summarizes rule scanning facts to form a preliminary audit judgment.",
        scoreLabel: "Initial Risk"
      },
      challenger: {
        title: "Challenger Review Agent",
        responsibility: "Independently challenges the preliminary audit conclusion, identifying over-judgments or missing evidence.",
        scoreLabel: "Adjusted Risk"
      },
      factCheck: {
        title: "Fact Check Agent",
        responsibility: "Maps conclusions back to original evidence, calculating support and conflict scores.",
        scoreLabel: "Support / Conflict"
      },
      partner: {
        title: "Senior Partner Agent",
        responsibility: "Synthesizes multi-party views, outputting final verdict and next audit steps.",
        scoreLabel: "Final Risk"
      }
    },
    agentStatus: {
      completed: "Completed",
      arbitrating: "Arbitrating",
      archived: "Archived"
    },
    relationsLabel: {
      support: "Support",
      conflict: "Conflict",
      security: "Security"
    },
    timelineData: [
      {
        stage: "01",
        title: "RAG Retrieval & Regulatory Basis Localization",
        description: "Retrieves payment approval, supplier management, and invoice filing rules to build compliance boundaries.",
        owner: "Rules & Knowledge Base"
      },
      {
        stage: "02",
        title: "Preliminary Audit & Risk Hypothesis",
        description: "Junior Audit Agent converts abnormal transactions into litigable preliminary conclusions and risk scores.",
        owner: "Junior Audit Agent"
      },
      {
        stage: "03",
        title: "Challenger Review & Game Triggering",
        description: "Challenger Review Agent searches for counterexamples, missing fields, and alternative explanations to prevent single-path misjudgments.",
        owner: "Challenger Review Agent"
      },
      {
        stage: "04",
        title: "Fact Check & Evidence Relations Generation",
        description: "Fact Check Agent binds viewpoints to evidence nodes, marking support and conflict edges.",
        owner: "Fact Check Agent"
      },
      {
        stage: "05",
        title: "Partner Arbitration & Action Output",
        description: "Senior Partner Agent yields the final audit action based on support, conflict, and risk exposure.",
        owner: "Senior Partner Agent"
      }
    ],
    dynamic: {
      risk: {
        high: "High Risk",
        medium: "Medium Risk",
        low: "Low Risk"
      },
      uploadedAudit: "Real-time uploaded file audit",
      unknownTime: "Unknown Time",
      noFindings: "No valid anomaly rule hits found",
      hasAnomaliesTitle: "Rule Review",
      noAnomaliesTitle: "Uploaded data did not trigger any anomaly rules",
      sourceSummaryAnomalies: "Based on your uploaded {file}, the system scanned {total} records, discovered {anomaly} anomalies, mainly hitting {finding}.",
      sourceSummaryNoAnomalies: "Based on your uploaded {file}, the system scanned {total} records, no rule-level anomalies found currently.",
      ruleHit: "{label} hit {count} records, supporting continued audit investigation.",
      ruleNotHit: "{label} not hit, reducing the certainty of this type of anomaly.",
      scanStatsContent: "Total records {total}, anomalies {anomaly}, highest amount {max}.",
      scanStatsMaxUnidentified: "Unidentified",
      privacyGuardContent: "The virtual audit group only reads rule summaries, statistics, and evidence nodes, not exposing raw sensitive field details.",
      evidenceEdgeScanStatsRationaleSupport: "The number of anomalies and amount exposure form the overall risk background.",
      evidenceEdgeScanStatsRationaleConflict: "Current scan statistics did not form clear anomaly pressure.",
      evidenceEdgePrivacyGuardRationale: "Collaborative presentation does not expose raw sensitive fields, meeting security closed-loop requirements.",
      juniorSummaryAnomalies: "Found {anomaly} anomalies, recommending review procedures.",
      juniorSummaryNoAnomalies: "Rule scanning found no anomalies, recommending archiving with sample records retention.",
      juniorAnalysisAnomalies: "The uploaded file has {total} records, rule layer discovered {finding}. The preliminary review suggests auditable anomalies exist, requiring multi-agent review.",
      juniorAnalysisNoAnomalies: "The uploaded file has {total} records, currently rule scanning has not hit anomalies, preliminary review leans towards low-risk archiving.",
      challengerSummaryAnomalies: "Risk signals are valid, but rule scanning still requires confirmation with business vouchers.",
      challengerSummaryNoAnomalies: "No rule anomalies seen, but still recommended to confirm field mapping and sample completeness.",
      challengerRebuttalAnomalies: "The Challenger argues that {finding} only proves rule hits, not direct fraud or erroneous entries; original vouchers, approval flows, and business context need to be supplemented.",
      challengerRebuttalNoAnomalies: "The Challenger did not find evidence to overturn the low-risk judgment, but reminds to confirm if the uploaded file covers the entire audit period.",
      factCheckSummaryAnomalies: "Rule facts support the anomaly judgment, conflicts mainly arise from incomplete business explanations.",
      factCheckSummaryNoAnomalies: "Fact layer did not form anomaly support, conflicts are centered around data completeness confirmation.",
      factCheckAnalysisAnomalies: "Fact checking maps {count} types of anomaly rules to evidence nodes. Support comes from rule hits and amount exposure, conflict comes from lack of voucher-level explanations.",
      factCheckAnalysisNoAnomalies: "Fact checking did not find rule hit nodes, supporting the low-risk conclusion; still need to confirm if field naming, amount columns, and duplicate row rules apply to this data.",
      partnerSummaryAnomalies: "Maintain anomaly judgment, entering special working papers and voucher supplement.",
      partnerSummaryNoAnomalies: "Anomaly not recognized for now, recommending archiving with sample review records retention.",
      partnerReasoningAnomalies: "Rule hits, anomaly counts, and amount exposure collectively support continuing the audit; the Challenger's opinions reduce certainty, but not enough to overturn the anomaly direction.",
      partnerReasoningNoAnomalies: "Rule scanning did not form sufficient support evidence, currently more suitable for low-risk archiving or re-evaluating after expanding the sample.",
      partnerActionAnomalies: "Generate special working papers, retrieving original vouchers, approval flows, and business descriptions.",
      partnerActionNoAnomalies: "Record this scan result, entering regular archiving after confirming data coverage.",
      finalDecisionReasoningAnomalies: "Multi-agents completed arbitration based on rule hit results of your uploaded file: {finding}, final risk score {score}/100.",
      finalDecisionReasoningNoAnomalies: "Multi-agents completed arbitration based on scan results of your uploaded file: currently insufficient evidence of anomalies, final risk score {score}/100.",
      finalDecisionActionAnomalies: "Generate special working papers and initiate voucher supplement requests to the business/finance team.",
      finalDecisionActionNoAnomalies: "Retain audit scan records, archiving according to standard flow.",
      unit: "records",
      separator: ", ",
      ruleReview: "Rule Review",
      scanStats: "Scan Stats",
      privacyAnonymization: "Presentation Layer Anonymization",
      enabled: "Enabled",
      backendPipelineSummary: "Backend multi-agent pipeline analyzed {total} records with consistency score {score}.",
      multiAgentTitle: "Multi-Agent Collaborative Virtual Audit Group",
      backendPipeline: "Backend Agent Pipeline"
    }
  },
  settings: {
    back: "Back to Console",
    title: "Model Configuration",
    subtitle: "Configure the LLM provider and model for the audit pipeline. Supports local models and various cloud APIs.",
    defaultTitle: "Default Model",
    defaultDesc: "All agents use this configuration by default, unless individually overridden.",
    provider: "Provider",
    apiKey: "API Key",
    baseUrl: "Base URL",
    model: "Model Name",
    agentOverride: "Per-Agent Override (Optional)",
    agentOverrideDesc: "Specify independent model configs for specific agents. Unconfigured agents will use the global default.",
    agentJunior: "Junior Auditor",
    agentChallenger: "Challenger",
    agentFactCheck: "Fact Checker",
    agentSenior: "Senior Partner",
    save: "Save Configuration",
    saving: "Saving...",
    saved: "Configuration Saved",
    saveFailed: "Save Failed",
    reset: "Reset",
    custom: "Custom",
    apiKeyPlaceholder: "Enter API Key",
    baseUrlPlaceholder: "Enter Base URL",
    modelPlaceholder: "Enter Model Name"
  }
};
