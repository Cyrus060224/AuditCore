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
import { useTranslation } from "../i18n";

type AgentRole = "junior" | "challenger" | "factCheck" | "partner";
type EvidenceRelation = "support" | "conflict" | "security";
type RiskLevel = string;
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
  status: string;
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

const RELATION_STYLE: Record<
  EvidenceRelation,
  { icon: typeof CheckCircle2; tone: string; line: string }
> = {
  support: {
    icon: CheckCircle2,
    tone: "bg-emerald-50 text-emerald-700",
    line: "border-emerald-200",
  },
  conflict: {
    icon: TriangleAlert,
    tone: "bg-amber-50 text-amber-700",
    line: "border-amber-200",
  },
  security: {
    icon: LockKeyhole,
    tone: "bg-sky-50 text-sky-700",
    line: "border-sky-200",
  },
};

function clampScore(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function formatDateTime(value: string, locale: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return locale === "zh" ? "未知时间" : "Unknown Time";
  return date.toLocaleString(locale === "zh" ? "zh-CN" : "en-US", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getRiskLevel(score: number, t: any): RiskLevel {
  if (score >= 70) return t("arena.dynamic.risk.high");
  if (score >= 35) return t("arena.dynamic.risk.medium");
  return t("arena.dynamic.risk.low");
}

function getPrimaryFinding(auditData: AuditData) {
  return auditData.rule_findings
    .filter((finding) => finding.record_count > 0)
    .sort((a, b) => b.record_count - a.record_count)[0];
}

function buildCouncilRun(session: UploadedAuditSession, t: any, locale: string): AuditCouncilRun {
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
  const riskLevel = getRiskLevel(finalRisk, t);
  const unit = locale === "zh" ? "条" : "records";
  const divider = locale === "zh" ? "、" : ", ";
  
  const findingText =
    activeFindings.length > 0
      ? activeFindings.map((finding) => `${finding.label} ${finding.record_count} ${unit}`).join(divider)
      : t("arena.dynamic.noFindings");
  const title = primaryFinding
    ? `${primaryFinding.label} ${locale === "zh" ? "规则复核" : "Rule Review"}`
    : t("arena.dynamic.noAnomaliesTitle");
  const sourceSummary = hasAnomalies
    ? t("arena.dynamic.sourceSummaryAnomalies", { file: fileName, total: totalRecords.toLocaleString(), anomaly: anomalyCount.toLocaleString(), finding: findingText })
    : t("arena.dynamic.sourceSummaryNoAnomalies", { file: fileName, total: totalRecords.toLocaleString() });

  const ruleNodes: EvidenceNode[] = auditData.rule_findings.map((finding, index) => ({
    node_id: `rule_fact_${index + 1}`,
    node_type: "RuleFinding",
    title: finding.label,
    content: `${finding.summary}。${t("arena.dynamic.ruleHit", { label: finding.label, count: finding.record_count })}`,
  }));

  const maxAmountStr = maxAmount > 0 ? `¥${maxAmount.toLocaleString()}` : t("arena.dynamic.scanStatsMaxUnidentified");

  const evidenceNodes: EvidenceNode[] = [
    ...ruleNodes,
    {
      node_id: "scan_stats",
      node_type: "AuditStats",
      title: locale === "zh" ? "扫描统计" : "Scan Stats",
      content: t("arena.dynamic.scanStatsContent", { total: totalRecords.toLocaleString(), anomaly: anomalyCount.toLocaleString(), max: maxAmountStr }),
    },
    {
      node_id: "privacy_01",
      node_type: "PrivacyGuard",
      title: locale === "zh" ? "展示层脱敏" : "Presentation Layer Anonymization",
      content: t("arena.dynamic.privacyGuardContent"),
    },
  ];

  const evidenceEdges: EvidenceEdge[] = [
    ...auditData.rule_findings.map((finding, index) => ({
      source_id: `rule_fact_${index + 1}`,
      target_id: "partner_verdict",
      relation: (finding.record_count > 0 ? "support" : "conflict") as EvidenceRelation,
      weight: finding.record_count > 0 ? Math.min(0.95, 0.45 + finding.record_count / Math.max(anomalyCount, 1) * 0.45) : 0.18,
      rationale:
        finding.record_count > 0
          ? t("arena.dynamic.ruleHit", { label: finding.label, count: finding.record_count })
          : t("arena.dynamic.ruleNotHit", { label: finding.label }),
    })),
    {
      source_id: "scan_stats",
      target_id: "partner_verdict",
      relation: hasAnomalies ? "support" : "conflict",
      weight: hasAnomalies ? Math.min(0.9, 0.5 + anomalyRate) : 0.3,
      rationale: hasAnomalies
        ? t("arena.dynamic.evidenceEdgeScanStatsRationaleSupport")
        : t("arena.dynamic.evidenceEdgeScanStatsRationaleConflict"),
    },
    {
      source_id: "privacy_01",
      target_id: "council_workspace",
      relation: "security",
      weight: 1,
      rationale: t("arena.dynamic.evidenceEdgePrivacyGuardRationale"),
    },
  ];

  const baseTimeline = [
    {
      stage: "01",
      title: t("arena.timelineData.0.title"),
      description: t("arena.timelineData.0.description"),
      owner: t("arena.timelineData.0.owner"),
    },
    {
      stage: "02",
      title: t("arena.timelineData.1.title"),
      description: t("arena.timelineData.1.description"),
      owner: t("arena.timelineData.1.owner"),
    },
    {
      stage: "03",
      title: t("arena.timelineData.2.title"),
      description: t("arena.timelineData.2.description"),
      owner: t("arena.timelineData.2.owner"),
    },
    {
      stage: "04",
      title: t("arena.timelineData.3.title"),
      description: t("arena.timelineData.3.description"),
      owner: t("arena.timelineData.3.owner"),
    },
    {
      stage: "05",
      title: t("arena.timelineData.4.title"),
      description: t("arena.timelineData.4.description"),
      owner: t("arena.timelineData.4.owner"),
    },
  ];

  return {
    caseId: `AC-${new Date(uploadedAt).getTime().toString().slice(-8)}`,
    title,
    scenario: t("arena.dynamic.uploadedAudit"),
    source: "uploaded",
    fileName,
    uploadedAt,
    sourceSummary,
    metrics: {
      total_records: totalRecords,
      anomaly_count: anomalyCount,
      exposure_amount: maxAmount,
      consistency_score: auditData.global_consistency_score,
      privacy_status: t("arena.loop.privacy") + " " + (locale === "zh" ? "已启用" : "Enabled"),
    },
    agents: [
      {
        id: "junior",
        title: t("arena.agentRoles.junior.title"),
        responsibility: t("arena.agentRoles.junior.responsibility"),
        status: t("arena.agentStatus.completed"),
        icon: FileSearch,
        scoreLabel: t("arena.agentRoles.junior.scoreLabel"),
        scoreValue: `${baseRisk}/100`,
        summary: hasAnomalies
          ? t("arena.dynamic.juniorSummaryAnomalies", { anomaly: anomalyCount })
          : t("arena.dynamic.juniorSummaryNoAnomalies"),
        output: {
          analysis: hasAnomalies
            ? t("arena.dynamic.juniorAnalysisAnomalies", { total: totalRecords, finding: findingText })
            : t("arena.dynamic.juniorAnalysisNoAnomalies", { total: totalRecords }),
          risk_score: baseRisk,
        },
      },
      {
        id: "challenger",
        title: t("arena.agentRoles.challenger.title"),
        responsibility: t("arena.agentRoles.challenger.responsibility"),
        status: t("arena.agentStatus.completed"),
        icon: MessageSquareWarning,
        scoreLabel: t("arena.agentRoles.challenger.scoreLabel"),
        scoreValue: `${challengeRisk}/100`,
        summary: hasAnomalies
          ? t("arena.dynamic.challengerSummaryAnomalies")
          : t("arena.dynamic.challengerSummaryNoAnomalies"),
        output: {
          rebuttal: hasAnomalies
            ? t("arena.dynamic.challengerRebuttalAnomalies", { finding: findingText })
            : t("arena.dynamic.challengerRebuttalNoAnomalies"),
          adjusted_risk_score: challengeRisk,
        },
      },
      {
        id: "factCheck",
        title: t("arena.agentRoles.factCheck.title"),
        responsibility: t("arena.agentRoles.factCheck.responsibility"),
        status: t("arena.agentStatus.completed"),
        icon: ShieldCheck,
        scoreLabel: t("arena.agentRoles.factCheck.scoreLabel"),
        scoreValue: `${supportScore.toFixed(2)} / ${conflictScore.toFixed(2)}`,
        summary: hasAnomalies
          ? t("arena.dynamic.factCheckSummaryAnomalies")
          : t("arena.dynamic.factCheckSummaryNoAnomalies"),
        output: {
          analysis: hasAnomalies
            ? t("arena.dynamic.factCheckAnalysisAnomalies", { count: activeFindings.length })
            : t("arena.dynamic.factCheckAnalysisNoAnomalies"),
          support_score: Number(supportScore.toFixed(2)),
          conflict_score: Number(conflictScore.toFixed(2)),
        },
      },
      {
        id: "partner",
        title: t("arena.agentRoles.partner.title"),
        responsibility: t("arena.agentRoles.partner.responsibility"),
        status: t("arena.agentStatus.archived"),
        icon: Gavel,
        scoreLabel: t("arena.agentRoles.partner.scoreLabel"),
        scoreValue: `${finalRisk}/100`,
        summary:
          finalVerdict === "True Anomaly"
            ? t("arena.dynamic.partnerSummaryAnomalies")
            : t("arena.dynamic.partnerSummaryNoAnomalies"),
        output: {
          final_verdict: finalVerdict,
          final_risk_score: finalRisk,
          reasoning:
            finalVerdict === "True Anomaly"
              ? t("arena.dynamic.partnerReasoningAnomalies")
              : t("arena.dynamic.partnerReasoningNoAnomalies"),
          action_item:
            finalVerdict === "True Anomaly"
              ? t("arena.dynamic.partnerActionAnomalies")
              : t("arena.dynamic.partnerActionNoAnomalies"),
        },
      },
    ],
    timeline: baseTimeline,
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
          ? t("arena.dynamic.finalDecisionReasoningAnomalies", { finding: findingText, score: finalRisk })
          : t("arena.dynamic.finalDecisionReasoningNoAnomalies", { score: finalRisk }),
      action_item:
        finalVerdict === "True Anomaly"
          ? t("arena.dynamic.finalDecisionActionAnomalies")
          : t("arena.dynamic.finalDecisionActionNoAnomalies"),
    },
  };
}

function readLatestAuditRun(t: any, locale: string): AuditCouncilRun | null {
  try {
    const raw = window.localStorage.getItem(LATEST_AUDIT_STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as UploadedAuditSession;
    if (!session.auditData || !session.fileName || !session.uploadedAt) return null;
    return buildCouncilRun(session, t, locale);
  } catch {
    return null;
  }
}

export default function AgentArena() {
  const { t, locale } = useTranslation();
  const [selectedAgentId, setSelectedAgentId] = useState<AgentRole>("junior");
  const [expandedDecision, setExpandedDecision] = useState(true);
  const [councilRun, setCouncilRun] = useState<AuditCouncilRun | null>(null);

  useEffect(() => {
    setCouncilRun(readLatestAuditRun(t, locale));
  }, [t, locale]);

  useEffect(() => {
    let cancelled = false;

    async function loadLatestAuditRun() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/audit/latest`);
        const payload = await response.json();
        if (!cancelled && response.ok && !("error" in payload)) {
          const run = buildCouncilRun(payload as UploadedAuditSession, t, locale);
          setCouncilRun(run);
          window.localStorage.setItem(LATEST_AUDIT_STORAGE_KEY, JSON.stringify(payload));
        }
      } catch {
        if (!cancelled) {
          setCouncilRun(readLatestAuditRun(t, locale));
        }
      }
    }

    function refreshLatestAuditRun() {
      setCouncilRun(readLatestAuditRun(t, locale));
    }

    loadLatestAuditRun();
    window.addEventListener("focus", refreshLatestAuditRun);
    window.addEventListener("storage", refreshLatestAuditRun);

    return () => {
      cancelled = true;
      window.removeEventListener("focus", refreshLatestAuditRun);
      window.removeEventListener("storage", refreshLatestAuditRun);
    };
  }, [t, locale]);

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
          {t("arena.back")}
        </Link>
      </div>

      <header className="mb-8 flex flex-col gap-5 border-b border-gray-100 pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-500">
            <Network size={13} />
            {t("arena.subtitleLabel")}
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-950">
            {councilRun.title}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-500">
            {councilRun.sourceSummary}
          </p>
          <p className="mt-2 text-xs text-gray-400">
            {t("arena.fileName", { file: councilRun.fileName, time: formatDateTime(councilRun.uploadedAt, locale) })}
          </p>
        </div>
        <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-4 lg:w-[520px]">
          <Metric label={t("arena.metrics.anomalies")} value={String(councilRun.metrics.anomaly_count)} />
          <Metric label={t("arena.metrics.exposure")} value={`¥${councilRun.metrics.exposure_amount.toLocaleString()}`} />
          <Metric label={t("arena.metrics.consistency")} value={councilRun.metrics.consistency_score.toFixed(2)} />
          <Metric label={t("arena.metrics.caseId")} value={councilRun.caseId} compact />
        </div>
      </header>

      <main className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-8">
          <section>
            <SectionTitle
              icon={Bot}
              title={t("arena.division.title")}
              description={t("arena.division.desc")}
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
              title={t("arena.timeline.title")}
              description={t("arena.timeline.desc")}
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
              title={t("arena.relations.title")}
              description={t("arena.relations.desc")}
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
  const { t } = useTranslation();
  return (
    <div className="animate-fade-in stagger-1">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          {t("arena.back")}
        </Link>
      </div>

      <div className="flex min-h-[56vh] flex-col items-center justify-center text-center">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-lg bg-gray-50">
          <Upload size={23} className="text-gray-500" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-gray-950">
          {t("arena.empty.title")}
        </h1>
        <p className="mt-3 max-w-md text-sm leading-6 text-gray-400">
          {t("arena.empty.desc")}
        </p>
        <Link
          href="/"
          className="mt-7 inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 cursor-pointer"
        >
          {t("arena.empty.btn")}
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
      className={`min-h-[156px] rounded-lg border p-4 text-left transition-colors cursor-pointer bg-white ${
        active
          ? "border-gray-400 bg-gray-50"
          : "border-gray-100 hover:border-gray-200 hover:bg-gray-50"
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
    <div className="grid gap-3 rounded-lg border border-gray-100 bg-white px-4 py-3 sm:grid-cols-[64px_minmax(0,1fr)_160px] sm:items-center">
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
    <div className="rounded-lg border border-gray-100 bg-white px-4 py-3">
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
  const { t } = useTranslation();
  const style = RELATION_STYLE[edge.relation];
  const Icon = style.icon;
  const label = t(`arena.relationsLabel.${edge.relation}`);

  return (
    <div className={`rounded-lg border bg-white px-4 py-3 ${style.line}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium ${style.tone}`}>
          <Icon size={13} />
          {label}
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
  const { t } = useTranslation();
  return (
    <section className="rounded-lg border border-gray-100 bg-white p-5">
      <div className="mb-4 flex items-center gap-2">
        <Brain size={16} className="text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-950">{t("arena.output.title")}</h2>
      </div>
      <p className="text-xs leading-5 text-gray-400">{agent.responsibility}</p>
      <div className="mt-5 rounded-lg bg-gray-50 p-4">
        <h3 className="text-sm font-semibold text-gray-950">{agent.title}</h3>
        <p className="mt-3 text-sm leading-6 text-gray-600">
          {agent.output.analysis ??
            agent.output.rebuttal ??
            agent.output.reasoning ??
            t("arena.output.empty")}
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
  const { t } = useTranslation();
  return (
    <section className="rounded-lg border border-gray-100 bg-white p-5">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 text-left cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <BadgeCheck size={16} className="text-emerald-600" />
          <h2 className="text-sm font-semibold text-gray-950">{t("arena.decision.title")}</h2>
        </div>
        {expanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
      </button>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <Metric label={t("arena.decision.verdict")} value={decision.final_verdict} compact />
        <Metric label={t("arena.decision.riskLevel")} value={decision.riskLevel} compact />
        <Metric label={t("arena.decision.finalScore")} value={`${decision.final_risk_score}/100`} compact />
        <Metric label={t("arena.decision.status")} value={t("arena.decision.archived")} compact />
      </div>
      {expanded && (
        <div className="mt-5 space-y-4">
          <div>
            <p className="text-xs font-medium text-gray-400">{t("arena.decision.basis")}</p>
            <p className="mt-2 text-sm leading-6 text-gray-600">{decision.reasoning}</p>
          </div>
          <div className="rounded-lg bg-emerald-50 p-4">
            <p className="text-xs font-medium text-emerald-700">{t("arena.decision.nextAction")}</p>
            <p className="mt-2 text-sm leading-6 text-emerald-900">{decision.action_item}</p>
          </div>
        </div>
      )}
    </section>
  );
}

function ClosedLoopPanel({ councilRun }: { councilRun: AuditCouncilRun }) {
  const { t } = useTranslation();
  const items = [
    { label: t("arena.loop.rag"), icon: Sparkles, status: t("arena.loop.ragStatus") },
    {
      label: t("arena.loop.hallucination"),
      icon: ShieldCheck,
      status: t("arena.loop.hallucinationStatus", {
        score: (councilRun.agents.find((agent) => agent.id === "factCheck")?.output.support_score ?? 0).toFixed(2)
      }),
    },
    { label: t("arena.loop.decision"), icon: Gavel, status: t("arena.loop.decisionStatus") },
    { label: t("arena.loop.privacy"), icon: LockKeyhole, status: councilRun.metrics.privacy_status },
  ];

  return (
    <section className="rounded-lg border border-gray-100 bg-white p-5">
      <div className="mb-4 flex items-center gap-2">
        <Network size={16} className="text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-950">{t("arena.loop.title")}</h2>
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
