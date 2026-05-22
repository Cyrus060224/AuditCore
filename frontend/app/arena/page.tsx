"use client";

import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Bot,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileSearch,
  GitBranch,
  Gavel,
  LockKeyhole,
  MessageSquareWarning,
  Network,
  Scale,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type AgentRole = "junior" | "challenger" | "factCheck" | "partner";
type EvidenceRelation = "support" | "conflict" | "security";
type RiskLevel = "高风险" | "中风险" | "低风险";
type DataSource = "uploaded" | "empty";

interface AuditData {
  global_consistency_score: number;
  current_state: string;
  consistency_threshold: number;
  stats: {
    total_records: number;
    anomaly_count: number;
    max_amount: number | null;
  };
  rule_findings: Array<{
    label: string;
    record_count: number;
    summary: string;
  }>;
  graph: {
    nodes: Array<{
      node_id: string;
      node_type: string;
      content: string;
    }>;
    edges: Array<{
      source_id: string;
      target_id: string;
      relation: string;
      weight: number;
    }>;
  };
}

interface UploadedAuditSession {
  fileName: string;
  uploadedAt: string;
  auditData: AuditData;
}

interface AuditCouncilAgent {
  id: AgentRole;
  title: string;
  responsibility: string;
  status: "已完成" | "仲裁中" | "已归档";
  icon: typeof Bot;
  scoreLabel: string;
  scoreValue: string;
  summary: string;
  output: {
    analysis?: string;
    risk_score?: number;
    rebuttal?: string;
    adjusted_risk_score?: number;
    support_score?: number;
    conflict_score?: number;
    final_verdict?: "True Anomaly" | "False Positive";
    final_risk_score?: number;
    reasoning?: string;
    action_item?: string;
  };
}

interface EvidenceNode {
  node_id: string;
  node_type: string;
  title: string;
  content: string;
}

interface EvidenceEdge {
  source_id: string;
  target_id: string;
  relation: EvidenceRelation;
  weight: number;
  rationale: string;
}

interface CouncilTimelineItem {
  stage: string;
  title: string;
  description: string;
  owner: string;
}

interface AuditCouncilRun {
  caseId: string;
  title: string;
  scenario: string;
  source: DataSource;
  fileName: string;
  uploadedAt: string;
  sourceSummary: string;
  metrics: {
    total_records: number;
    anomaly_count: number;
    exposure_amount: number;
    consistency_score: number;
    privacy_status: string;
  };
  agents: AuditCouncilAgent[];
  timeline: CouncilTimelineItem[];
  evidence: {
    nodes: EvidenceNode[];
    edges: EvidenceEdge[];
  };
  finalDecision: {
    final_verdict: "True Anomaly" | "False Positive";
    riskLevel: RiskLevel;
    final_risk_score: number;
    reasoning: string;
    action_item: string;
  };
}

const LATEST_AUDIT_STORAGE_KEY = "auditcore.latestAuditRun";
const API_BASE_URL =
  process.env.NEXT_PUBLIC_AUDIT_API_BASE_URL ?? "http://127.0.0.1:8000";

const BASE_TIMELINE: CouncilTimelineItem[] = [
    {
      stage: "01",
      title: "RAG 检索定位制度依据",
      description: "检索付款审批、供应商管理和发票归档规则，为后续判断建立依据边界。",
      owner: "规则与知识库",
    },
    {
      stage: "02",
      title: "初审形成风险假设",
      description: "初级审计 Agent 将异常流水转化为可质证的初步结论和风险评分。",
      owner: "初级审计 Agent",
    },
    {
      stage: "03",
      title: "反方复核触发博弈",
      description: "反方复核 Agent 专门寻找反例、遗漏字段和替代解释，防止单一路径误判。",
      owner: "反方复核 Agent",
    },
    {
      stage: "04",
      title: "事实核查生成证据关系",
      description: "Fact-checking Agent 把观点绑定到证据节点，标记支持边与冲突边。",
      owner: "事实核查 Agent",
    },
    {
      stage: "05",
      title: "合伙人仲裁输出动作",
      description: "高级合伙人 Agent 根据支持度、冲突度和风险暴露给出最终审计动作。",
      owner: "高级合伙人 Agent",
    },
];

const RELATION_STYLE: Record<
  EvidenceRelation,
  { label: string; icon: typeof CheckCircle2; tone: string; line: string }
> = {
  support: {
    label: "支持",
    icon: CheckCircle2,
    tone: "bg-emerald-50 text-emerald-700",
    line: "border-emerald-200",
  },
  conflict: {
    label: "冲突",
    icon: TriangleAlert,
    tone: "bg-amber-50 text-amber-700",
    line: "border-amber-200",
  },
  security: {
    label: "安全",
    icon: LockKeyhole,
    tone: "bg-sky-50 text-sky-700",
    line: "border-sky-200",
  },
};

function clampScore(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getRiskLevel(score: number): RiskLevel {
  if (score >= 70) return "高风险";
  if (score >= 35) return "中风险";
  return "低风险";
}

function getPrimaryFinding(auditData: AuditData) {
  return auditData.rule_findings
    .filter((finding) => finding.record_count > 0)
    .sort((a, b) => b.record_count - a.record_count)[0];
}

function buildCouncilRun(session: UploadedAuditSession): AuditCouncilRun {
  const { auditData, fileName, uploadedAt } = session;
  const totalRecords = auditData.stats.total_records;
  const anomalyCount = auditData.stats.anomaly_count;
  const maxAmount = auditData.stats.max_amount ?? 0;
  const anomalyRate = totalRecords > 0 ? anomalyCount / totalRecords : 0;
  const primaryFinding = getPrimaryFinding(auditData);
  const activeFindings = auditData.rule_findings.filter((finding) => finding.record_count > 0);
  const hasAnomalies = anomalyCount > 0;
  const baseRisk = clampScore(anomalyRate * 180 + Math.min(maxAmount / 100000, 1) * 18 + (hasAnomalies ? 28 : 8));
  const challengeRisk = clampScore(baseRisk - (activeFindings.length <= 1 ? 12 : 7));
  const supportScore = Math.max(0.35, Math.min(0.95, anomalyCount > 0 ? 0.58 + Math.min(anomalyRate * 1.8, 0.28) : 0.38));
  const conflictScore = Math.max(0.05, Math.min(0.45, activeFindings.length <= 1 ? 0.28 : 0.16));
  const finalRisk = clampScore(baseRisk * 0.55 + challengeRisk * 0.25 + supportScore * 20 - conflictScore * 10);
  const finalVerdict = finalRisk >= 45 ? "True Anomaly" : "False Positive";
  const riskLevel = getRiskLevel(finalRisk);
  const findingText =
    activeFindings.length > 0
      ? activeFindings.map((finding) => `${finding.label} ${finding.record_count} 条`).join("、")
      : "未发现有效异常规则命中";
  const title = primaryFinding
    ? `${primaryFinding.label} 规则复核`
    : "上传数据未触发异常规则";
  const sourceSummary = hasAnomalies
    ? `基于你上传的 ${fileName}，系统扫描 ${totalRecords.toLocaleString()} 条记录，发现 ${anomalyCount.toLocaleString()} 条异常，主要命中 ${findingText}。`
    : `基于你上传的 ${fileName}，系统扫描 ${totalRecords.toLocaleString()} 条记录，当前未发现规则层异常。`;

  const ruleNodes: EvidenceNode[] = auditData.rule_findings.map((finding, index) => ({
    node_id: `rule_fact_${index + 1}`,
    node_type: "RuleFinding",
    title: finding.label,
    content: `${finding.summary}。该规则命中 ${finding.record_count} 条记录。`,
  }));

  const evidenceNodes: EvidenceNode[] = [
    ...ruleNodes,
    {
      node_id: "scan_stats",
      node_type: "AuditStats",
      title: "扫描统计",
      content: `总记录 ${totalRecords.toLocaleString()} 条，异常 ${anomalyCount.toLocaleString()} 条，最高金额 ${
        maxAmount > 0 ? `¥${maxAmount.toLocaleString()}` : "未识别"
      }。`,
    },
    {
      node_id: "privacy_01",
      node_type: "PrivacyGuard",
      title: "展示层脱敏",
      content: "虚拟审计组只读取规则摘要、统计值和证据节点，不展示原始敏感字段明细。",
    },
  ];

  const evidenceEdges: EvidenceEdge[] = [
    ...auditData.rule_findings.map((finding, index) => ({
      source_id: `rule_fact_${index + 1}`,
      target_id: "partner_verdict",
      relation: finding.record_count > 0 ? "support" as EvidenceRelation : "conflict" as EvidenceRelation,
      weight: finding.record_count > 0 ? Math.min(0.95, 0.45 + finding.record_count / Math.max(anomalyCount, 1) * 0.45) : 0.18,
      rationale:
        finding.record_count > 0
          ? `${finding.label} 命中 ${finding.record_count} 条记录，支持继续审计追查。`
          : `${finding.label} 未命中，降低该类异常的确定性。`,
    })),
    {
      source_id: "scan_stats",
      target_id: "partner_verdict",
      relation: hasAnomalies ? "support" : "conflict",
      weight: hasAnomalies ? Math.min(0.9, 0.5 + anomalyRate) : 0.3,
      rationale: hasAnomalies
        ? "异常数量和金额暴露形成整体风险背景。"
        : "当前扫描统计未形成明显异常压力。",
    },
    {
      source_id: "privacy_01",
      target_id: "council_workspace",
      relation: "security",
      weight: 1,
      rationale: "协作展示不暴露原始敏感字段，满足安全闭环要求。",
    },
  ];

  return {
    caseId: `AC-${new Date(uploadedAt).getTime().toString().slice(-8)}`,
    title,
    scenario: "上传文件实时审计",
    source: "uploaded",
    fileName,
    uploadedAt,
    sourceSummary,
    metrics: {
      total_records: totalRecords,
      anomaly_count: anomalyCount,
      exposure_amount: maxAmount,
      consistency_score: auditData.global_consistency_score,
      privacy_status: "展示层脱敏已启用",
    },
    agents: [
      {
        id: "junior",
        title: "初级审计 Agent",
        responsibility: "汇总规则扫描事实，形成初步审计判断。",
        status: "已完成",
        icon: FileSearch,
        scoreLabel: "初始风险",
        scoreValue: `${baseRisk}/100`,
        summary: hasAnomalies
          ? `发现 ${anomalyCount} 条异常，建议进入复核程序。`
          : "规则扫描未发现异常，建议归档并保留抽样记录。",
        output: {
          analysis: hasAnomalies
            ? `上传文件共 ${totalRecords} 条记录，规则层发现 ${findingText}。初审认为该批数据存在可审计异常，需要进入多 Agent 复核。`
            : `上传文件共 ${totalRecords} 条记录，当前规则扫描未命中异常，初审倾向于低风险归档。`,
          risk_score: baseRisk,
        },
      },
      {
        id: "challenger",
        title: "反方复核 Agent",
        responsibility: "独立质疑初审结论，识别过度判断或遗漏证据。",
        status: "已完成",
        icon: MessageSquareWarning,
        scoreLabel: "调整风险",
        scoreValue: `${challengeRisk}/100`,
        summary: hasAnomalies
          ? "风险信号成立，但规则扫描仍需结合业务凭证确认。"
          : "未见规则异常，但仍建议确认字段映射和样本完整性。",
        output: {
          rebuttal: hasAnomalies
            ? `反方认为 ${findingText} 只能证明规则命中，尚不能直接证明舞弊或错误入账；需补充原始凭证、审批流和业务背景。`
            : "反方未发现可推翻低风险判断的证据，但提醒应确认上传文件是否覆盖完整审计期间。",
          adjusted_risk_score: challengeRisk,
        },
      },
      {
        id: "factCheck",
        title: "事实核查 Agent",
        responsibility: "将结论映射回原始证据，计算支持度与冲突度。",
        status: "已完成",
        icon: ShieldCheck,
        scoreLabel: "支持 / 冲突",
        scoreValue: `${supportScore.toFixed(2)} / ${conflictScore.toFixed(2)}`,
        summary: hasAnomalies
          ? "规则事实支持异常判断，冲突主要来自业务解释尚未补齐。"
          : "事实层未形成异常支持，冲突点集中在数据完整性确认。",
        output: {
          analysis: hasAnomalies
            ? `事实核查将 ${activeFindings.length} 类异常规则映射为证据节点。支持度来自规则命中和金额暴露，冲突度来自缺少凭证级解释。`
            : "事实核查未找到规则命中节点，支持低风险结论；仍需确认字段命名、金额列和重复行规则是否适用于本数据。",
          support_score: Number(supportScore.toFixed(2)),
          conflict_score: Number(conflictScore.toFixed(2)),
        },
      },
      {
        id: "partner",
        title: "高级合伙人 Agent",
        responsibility: "综合多方观点，输出最终裁决和下一步审计动作。",
        status: "已归档",
        icon: Gavel,
        scoreLabel: "最终风险",
        scoreValue: `${finalRisk}/100`,
        summary:
          finalVerdict === "True Anomaly"
            ? "维持异常判断，进入专项底稿和凭证补证。"
            : "暂不认定异常，建议归档并保留抽样复核记录。",
        output: {
          final_verdict: finalVerdict,
          final_risk_score: finalRisk,
          reasoning:
            finalVerdict === "True Anomaly"
              ? `规则命中、异常数量和金额暴露共同支持继续审计；反方意见降低确定性，但不足以推翻异常方向。`
              : "规则扫描未形成足够支持证据，当前更适合低风险归档或扩大样本后再评估。",
          action_item:
            finalVerdict === "True Anomaly"
              ? "生成专项审计底稿，调取原始凭证、审批流和业务说明。"
              : "记录本次扫描结果，确认数据覆盖范围后进入常规归档。",
        },
      },
    ],
    timeline: BASE_TIMELINE,
    evidence: {
      nodes: evidenceNodes,
      edges: evidenceEdges,
    },
    finalDecision: {
      final_verdict: finalVerdict,
      riskLevel,
      final_risk_score: finalRisk,
      reasoning:
        finalVerdict === "True Anomaly"
          ? `多 Agent 根据你上传文件的规则命中结果完成仲裁：${findingText}，最终风险分 ${finalRisk}/100。`
          : `多 Agent 根据你上传文件的扫描结果完成仲裁：当前异常证据不足，最终风险分 ${finalRisk}/100。`,
      action_item:
        finalVerdict === "True Anomaly"
          ? "生成专项审计底稿，并向业务/财务团队发起凭证补证请求。"
          : "保留审计扫描记录，按常规流程归档。",
    },
  };
}

function readLatestAuditRun(): AuditCouncilRun | null {
  try {
    const raw = window.localStorage.getItem(LATEST_AUDIT_STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as UploadedAuditSession;
    if (!session.auditData || !session.fileName || !session.uploadedAt) return null;
    return buildCouncilRun(session);
  } catch {
    return null;
  }
}

export default function AgentArena() {
  const [selectedAgentId, setSelectedAgentId] = useState<AgentRole>("junior");
  const [expandedDecision, setExpandedDecision] = useState(true);
  const [councilRun, setCouncilRun] = useState<AuditCouncilRun | null>(() => {
    if (typeof window === "undefined") return null;
    return readLatestAuditRun();
  });

  useEffect(() => {
    let cancelled = false;

    async function loadLatestAuditRun() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/audit/latest`);
        const payload = await response.json();
        if (!cancelled && response.ok && !("error" in payload)) {
          const run = buildCouncilRun(payload as UploadedAuditSession);
          setCouncilRun(run);
          window.localStorage.setItem(LATEST_AUDIT_STORAGE_KEY, JSON.stringify(payload));
        }
      } catch {
        if (!cancelled) {
          setCouncilRun(readLatestAuditRun());
        }
      }
    }

    function refreshLatestAuditRun() {
      setCouncilRun(readLatestAuditRun());
    }

    loadLatestAuditRun();
    window.addEventListener("focus", refreshLatestAuditRun);
    window.addEventListener("storage", refreshLatestAuditRun);

    return () => {
      cancelled = true;
      window.removeEventListener("focus", refreshLatestAuditRun);
      window.removeEventListener("storage", refreshLatestAuditRun);
    };
  }, []);

  const selectedAgent = useMemo(
    () =>
      councilRun?.agents.find((agent) => agent.id === selectedAgentId) ??
      councilRun?.agents[0] ??
      null,
    [councilRun, selectedAgentId]
  );

  if (!councilRun || !selectedAgent) {
    return <EmptyArena />;
  }

  return (
    <div className="animate-fade-in stagger-1">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          返回控制台
        </Link>
      </div>

      <header className="mb-8 flex flex-col gap-5 border-b border-gray-100 pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-500">
            <Network size={13} />
            多 Agent 协作虚拟审计组
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-950">
            {councilRun.title}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-500">
            {councilRun.sourceSummary}
          </p>
          <p className="mt-2 text-xs text-gray-400">
            数据来源：{councilRun.fileName} · 上传时间 {formatDateTime(councilRun.uploadedAt)}
          </p>
        </div>
        <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-4 lg:w-[520px]">
          <Metric label="异常记录" value={String(councilRun.metrics.anomaly_count)} />
          <Metric label="风险暴露" value={`¥${councilRun.metrics.exposure_amount.toLocaleString()}`} />
          <Metric label="一致性" value={councilRun.metrics.consistency_score.toFixed(2)} />
          <Metric label="案例编号" value={councilRun.caseId} compact />
        </div>
      </header>

      <main className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-8">
          <section>
            <SectionTitle
              icon={Bot}
              title="审计组分工"
              description="四类 Agent 按审计职责拆分观点、质疑、核验和裁决。"
            />
            <div className="grid gap-3 md:grid-cols-2">
              {councilRun.agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  active={agent.id === selectedAgentId}
                  onSelect={() => setSelectedAgentId(agent.id)}
                />
              ))}
            </div>
          </section>

          <section>
            <SectionTitle
              icon={GitBranch}
              title="协作时间线"
              description="从制度检索到最终仲裁，保留每一步可解释的决策轨迹。"
            />
            <div className="space-y-3">
              {councilRun.timeline.map((item) => (
                <TimelineRow key={item.stage} item={item} />
              ))}
            </div>
          </section>

          <section>
            <SectionTitle
              icon={Scale}
              title="证据支持与冲突关系"
              description="用轻量证据图表达事实节点如何影响最终裁决。"
            />
            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <div className="space-y-3">
                {councilRun.evidence.nodes.map((node) => (
                  <EvidenceNodeCard key={node.node_id} node={node} />
                ))}
              </div>
              <div className="space-y-3">
                {councilRun.evidence.edges.map((edge) => (
                  <EvidenceEdgeCard key={`${edge.source_id}-${edge.target_id}`} edge={edge} />
                ))}
              </div>
            </div>
          </section>
        </div>

        <aside className="space-y-6">
          <AgentDetail agent={selectedAgent} />
          <FinalDecision
            decision={councilRun.finalDecision}
            expanded={expandedDecision}
            onToggle={() => setExpandedDecision((value) => !value)}
          />
          <ClosedLoopPanel councilRun={councilRun} />
        </aside>
      </main>
    </div>
  );
}

function Metric({
  label,
  value,
  compact = false,
}: {
  label: string;
  value: string;
  compact?: boolean;
}) {
  return (
    <div className="min-w-0 border-l border-gray-100 pl-3">
      <p className="text-[11px] font-medium text-gray-400">{label}</p>
      <p
        className={`mt-1 font-semibold tracking-tight text-gray-950 ${
          compact ? "break-words text-sm leading-5" : "truncate text-lg"
        }`}
        title={value}
      >
        {value}
      </p>
    </div>
  );
}

function EmptyArena() {
  return (
    <div className="animate-fade-in stagger-1">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          返回控制台
        </Link>
      </div>

      <div className="flex min-h-[56vh] flex-col items-center justify-center text-center">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-lg bg-gray-50">
          <Upload size={23} className="text-gray-500" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-gray-950">
          请先上传审计文件
        </h1>
        <p className="mt-3 max-w-md text-sm leading-6 text-gray-400">
          虚拟审计组现在读取最近一次 Excel 上传结果，并基于真实规则扫描结果生成多 Agent 分析。
        </p>
        <Link
          href="/"
          className="mt-7 inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50"
        >
          上传 .xlsx 文件
          <ArrowRight size={15} />
        </Link>
      </div>
    </div>
  );
}

function SectionTitle({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Bot;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-4 flex items-start gap-2.5">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gray-50">
        <Icon size={15} className="text-gray-500" />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-gray-950">{title}</h2>
        <p className="mt-1 text-xs leading-5 text-gray-400">{description}</p>
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  active,
  onSelect,
}: {
  agent: AuditCouncilAgent;
  active: boolean;
  onSelect: () => void;
}) {
  const Icon = agent.icon;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`min-h-[156px] rounded-lg border p-4 text-left transition-colors ${
        active
          ? "border-gray-400 bg-gray-50"
          : "border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white ring-1 ring-gray-100">
            <Icon size={17} className="text-gray-700" />
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-gray-950">{agent.title}</h3>
            <p className="mt-1 text-xs text-gray-400">{agent.status}</p>
          </div>
        </div>
        <ArrowRight
          size={15}
          className={`mt-2 shrink-0 ${active ? "text-gray-700" : "text-gray-300"}`}
        />
      </div>
      <p className="mt-4 text-sm leading-6 text-gray-600">{agent.summary}</p>
      <div className="mt-4 flex items-center justify-between gap-3 border-t border-gray-100 pt-3">
        <span className="text-xs text-gray-400">{agent.scoreLabel}</span>
        <span className="text-sm font-semibold text-gray-950">{agent.scoreValue}</span>
      </div>
    </button>
  );
}

function TimelineRow({ item }: { item: CouncilTimelineItem }) {
  return (
    <div className="grid gap-3 rounded-lg border border-gray-100 px-4 py-3 sm:grid-cols-[64px_minmax(0,1fr)_160px] sm:items-center">
      <span className="font-mono text-xs font-semibold text-gray-400">{item.stage}</span>
      <div className="min-w-0">
        <h3 className="text-sm font-medium text-gray-950">{item.title}</h3>
        <p className="mt-1 text-xs leading-5 text-gray-500">{item.description}</p>
      </div>
      <span className="text-xs font-medium text-gray-400 sm:text-right">{item.owner}</span>
    </div>
  );
}

function EvidenceNodeCard({ node }: { node: EvidenceNode }) {
  return (
    <div className="rounded-lg border border-gray-100 px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-gray-950">{node.title}</h3>
          <p className="mt-1 font-mono text-[11px] text-gray-400">{node.node_id}</p>
        </div>
        <span className="shrink-0 rounded-md bg-gray-50 px-2 py-1 text-[11px] font-medium text-gray-500">
          {node.node_type}
        </span>
      </div>
      <p className="mt-3 text-xs leading-5 text-gray-500">{node.content}</p>
    </div>
  );
}

function EvidenceEdgeCard({ edge }: { edge: EvidenceEdge }) {
  const style = RELATION_STYLE[edge.relation];
  const Icon = style.icon;

  return (
    <div className={`rounded-lg border px-4 py-3 ${style.line}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium ${style.tone}`}>
          <Icon size={13} />
          {style.label}
        </span>
        <span className="font-mono text-xs text-gray-400">{edge.source_id}</span>
        <ArrowRight size={13} className="text-gray-300" />
        <span className="font-mono text-xs text-gray-400">{edge.target_id}</span>
      </div>
      <p className="mt-3 text-xs leading-5 text-gray-500">{edge.rationale}</p>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full ${
            edge.relation === "conflict"
              ? "bg-amber-400"
              : edge.relation === "security"
              ? "bg-sky-400"
              : "bg-emerald-500"
          }`}
          style={{ width: `${Math.round(edge.weight * 100)}%` }}
        />
      </div>
    </div>
  );
}

function AgentDetail({ agent }: { agent: AuditCouncilAgent }) {
  return (
    <section className="rounded-lg border border-gray-100 p-5">
      <div className="mb-4 flex items-center gap-2">
        <Brain size={16} className="text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-950">当前 Agent 输出</h2>
      </div>
      <p className="text-xs leading-5 text-gray-400">{agent.responsibility}</p>
      <div className="mt-5 rounded-lg bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-950">{agent.title}</h3>
        <p className="mt-3 text-sm leading-6 text-gray-600">
          {agent.output.analysis ??
            agent.output.rebuttal ??
            agent.output.reasoning ??
            "暂无输出。"}
        </p>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3">
        {Object.entries(agent.output)
          .filter(([key]) => key !== "analysis" && key !== "rebuttal" && key !== "reasoning")
          .map(([key, value]) => (
            <div key={key} className="min-w-0 border-l border-gray-100 pl-3">
              <dt className="truncate font-mono text-[11px] text-gray-400">{key}</dt>
              <dd className="mt-1 truncate text-sm font-semibold text-gray-950">{String(value)}</dd>
            </div>
          ))}
      </dl>
    </section>
  );
}

function FinalDecision({
  decision,
  expanded,
  onToggle,
}: {
  decision: AuditCouncilRun["finalDecision"];
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <section className="rounded-lg border border-gray-100 p-5">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 text-left"
      >
        <div className="flex items-center gap-2">
          <BadgeCheck size={16} className="text-emerald-600" />
          <h2 className="text-sm font-semibold text-gray-950">最终仲裁</h2>
        </div>
        {expanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
      </button>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <Metric label="裁决" value={decision.final_verdict} compact />
        <Metric label="风险等级" value={decision.riskLevel} compact />
        <Metric label="最终风险分" value={`${decision.final_risk_score}/100`} compact />
        <Metric label="输出状态" value="已归档" compact />
      </div>
      {expanded && (
        <div className="mt-5 space-y-4">
          <div>
            <p className="text-xs font-medium text-gray-400">仲裁依据</p>
            <p className="mt-2 text-sm leading-6 text-gray-600">{decision.reasoning}</p>
          </div>
          <div className="rounded-lg bg-emerald-50 p-4">
            <p className="text-xs font-medium text-emerald-700">下一步审计动作</p>
            <p className="mt-2 text-sm leading-6 text-emerald-900">{decision.action_item}</p>
          </div>
        </div>
      )}
    </section>
  );
}

function ClosedLoopPanel({ councilRun }: { councilRun: AuditCouncilRun }) {
  const items = [
    { label: "RAG 路径优化", icon: Sparkles, status: "制度依据已检索" },
    {
      label: "防幻觉核查",
      icon: ShieldCheck,
      status: `证据支持度 ${(
        councilRun.agents.find((agent) => agent.id === "factCheck")?.output.support_score ?? 0
      ).toFixed(2)}`,
    },
    { label: "多 Agent 决策", icon: Gavel, status: "仲裁结论已形成" },
    { label: "隐私脱敏", icon: LockKeyhole, status: councilRun.metrics.privacy_status },
  ];

  return (
    <section className="rounded-lg border border-gray-100 p-5">
      <div className="mb-4 flex items-center gap-2">
        <Network size={16} className="text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-950">技术闭环状态</h2>
      </div>
      <div className="space-y-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-50">
                <Icon size={15} className="text-gray-500" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-950">{item.label}</p>
                <p className="truncate text-xs text-gray-400">{item.status}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
