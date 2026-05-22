"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clipboard,
  Download,
  FileText,
  RefreshCw,
  TriangleAlert,
  Upload,
} from "lucide-react";
import { useTranslation } from "../i18n";

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

type LoadState = "loading" | "ready" | "empty" | "error";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_AUDIT_API_BASE_URL ?? "http://127.0.0.1:8000";

function formatDateTime(value: string, locale: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return locale === "zh" ? "未知时间" : "Unknown Time";
  return date.toLocaleString(locale === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getRiskLabel(data: AuditData, t: any) {
  if (data.stats.anomaly_count >= 5) return t("papers.risk.high");
  if (data.stats.anomaly_count > 0) return t("papers.risk.medium");
  return t("papers.risk.low");
}

function buildWorkingPaper(session: UploadedAuditSession, t: any, locale: string) {
  const { auditData, fileName, uploadedAt } = session;
  const findings = auditData.rule_findings;
  const activeFindings = findings.filter((finding) => finding.record_count > 0);
  const maxAmount =
    auditData.stats.max_amount == null
      ? t("papers.risk.unidentified")
      : `¥${auditData.stats.max_amount.toLocaleString()}`;

  const findingLines =
    findings.length > 0
      ? findings
          .map(
            (finding) =>
              `- ${finding.label}: ${t("papers.findings.items", { count: finding.record_count })}；${finding.summary}`
          )
          .join("\n")
      : `- ${t("papers.doc.emptyFindings")}`;

  const evidenceLines =
    auditData.graph.nodes.length > 0
      ? auditData.graph.nodes
          .map((node) => `- ${node.node_id} / ${node.node_type}: ${node.content}`)
          .join("\n")
      : activeFindings
          .map(
            (finding, index) =>
              `- rule_fact_${index + 1} / RuleFinding: ${finding.summary}`
          )
          .join("\n") || `- ${t("papers.doc.emptyEvidence")}`;

  const conclusion =
    auditData.stats.anomaly_count > 0
      ? t("papers.doc.conclusionPositive")
      : t("papers.doc.conclusionNegative");

  const nextActions =
    auditData.stats.anomaly_count > 0
      ? t("papers.doc.actionPositive")
      : t("papers.doc.actionNegative");

  return `# ${t("papers.doc.title")}

## ${t("papers.doc.section1")}
- ${t("papers.doc.fileName")}: ${fileName}
- ${t("papers.doc.uploadedAt")}: ${formatDateTime(uploadedAt, locale)}
- ${t("papers.doc.source")}: ${t("papers.doc.sourceVal")}

## ${t("papers.doc.section2")}
- ${t("papers.doc.scanned")}: ${auditData.stats.total_records}
- ${t("papers.doc.anomalies")}: ${auditData.stats.anomaly_count}
- ${t("papers.doc.exposure")}: ${maxAmount}
- ${t("papers.doc.consistency")}: ${auditData.global_consistency_score.toFixed(2)}
- ${t("papers.doc.riskLevel")}: ${getRiskLabel(auditData, t)}

## ${t("papers.doc.section3")}
${findingLines}

## ${t("papers.doc.section4")}
${evidenceLines}

## ${t("papers.doc.section5")}
${conclusion}

## ${t("papers.doc.section6")}
${nextActions}
`;
}

export default function WorkingPapers() {
  const { t, locale } = useTranslation();
  const [session, setSession] = useState<UploadedAuditSession | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [copyStatus, setCopyStatus] = useState<string>("");

  useEffect(() => {
    setCopyStatus(t("papers.copyPaper"));
  }, [t]);

  const workingPaper = useMemo(
    () => (session ? buildWorkingPaper(session, t, locale) : ""),
    [session, t, locale]
  );

  async function loadLatestAudit() {
    setLoadState("loading");
    setCopyStatus(t("papers.copyPaper"));

    try {
      const response = await fetch(`${API_BASE_URL}/api/audit/latest`);
      const payload = await response.json();

      if (!response.ok || "error" in payload) {
        setSession(null);
        setLoadState("empty");
        return;
      }

      setSession(payload as UploadedAuditSession);
      setLoadState("ready");
    } catch {
      setSession(null);
      setLoadState("error");
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function loadInitialAudit() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/audit/latest`);
        const payload = await response.json();

        if (cancelled) return;

        if (!response.ok || "error" in payload) {
          setSession(null);
          setLoadState("empty");
          return;
        }

        setSession(payload as UploadedAuditSession);
        setLoadState("ready");
      } catch {
        if (!cancelled) {
          setSession(null);
          setLoadState("error");
        }
      }
    }

    loadInitialAudit();

    return () => {
      cancelled = true;
    };
  }, []);

  async function copyWorkingPaper() {
    if (!workingPaper) return;
    try {
      await navigator.clipboard.writeText(workingPaper);
      setCopyStatus(t("papers.copied"));
    } catch {
      setCopyStatus(t("papers.copyFailed"));
    }
  }

  function downloadWorkingPaper() {
    if (!session || !workingPaper) return;
    const blob = new Blob([workingPaper], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${session.fileName.replace(/\.xlsx$/i, "")}-working-paper.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  if (loadState === "empty") {
    return <EmptyPapers />;
  }

  if (loadState === "error") {
    return (
      <StateMessage
        icon={TriangleAlert}
        title={t("papers.error.title")}
        description={t("papers.error.desc", { url: API_BASE_URL })}
        actionLabel={t("papers.error.btn")}
        onAction={loadLatestAudit}
      />
    );
  }

  if (loadState === "loading" || !session) {
    return (
      <StateMessage
        icon={RefreshCw}
        title={t("papers.loading.title")}
        description={t("papers.loading.desc")}
      />
    );
  }

  const auditData = session.auditData;
  const riskLabel = getRiskLabel(auditData, t);

  return (
    <div className="animate-fade-in stagger-1">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          {t("papers.back")}
        </Link>
      </div>

      <header className="mb-8 flex flex-col gap-5 border-b border-gray-100 pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-500">
            <FileText size={13} />
            {t("papers.title")}
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-950">
            {session.fileName}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-500">
            {t("papers.subtitle")}
          </p>
          <p className="mt-2 text-xs text-gray-400">
            {t("papers.uploadedAt", { time: formatDateTime(session.uploadedAt, locale) })}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={loadLatestAudit}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={15} />
            {t("papers.refresh")}
          </button>
          <button
            type="button"
            onClick={copyWorkingPaper}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 cursor-pointer"
          >
            <Clipboard size={15} />
            {copyStatus || t("papers.copyPaper")}
          </button>
          <button
            type="button"
            onClick={downloadWorkingPaper}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-gray-950 px-3.5 text-sm font-medium text-white transition-colors hover:bg-gray-800 cursor-pointer"
          >
            <Download size={15} />
            {t("papers.downloadMd")}
          </button>
        </div>
      </header>

      <div className="mb-8 grid gap-6 sm:grid-cols-4">
        <Metric label={t("papers.metrics.scanned")} value={String(auditData.stats.total_records)} />
        <Metric label={t("papers.metrics.anomalies")} value={String(auditData.stats.anomaly_count)} />
        <Metric
          label={t("papers.metrics.exposure")}
          value={
            auditData.stats.max_amount == null
              ? t("papers.risk.unidentified")
              : `¥${auditData.stats.max_amount.toLocaleString()}`
          }
        />
        <Metric label={t("papers.metrics.riskLevel")} value={riskLabel} />
      </div>

      <main className="grid gap-8 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <section>
          <SectionTitle title={t("papers.findings.title")} description={t("papers.findings.desc")} />
          <div className="space-y-3">
            {auditData.rule_findings.map((finding) => (
              <div key={finding.label} className="rounded-lg border border-gray-100 px-4 py-3 bg-white">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-sm font-semibold text-gray-950">
                      {finding.label}
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-gray-500">
                      {finding.summary}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-md px-2 py-1 text-xs font-medium ${
                      finding.record_count > 0
                        ? "bg-amber-50 text-amber-700"
                        : "bg-emerald-50 text-emerald-700"
                    }`}
                  >
                    {t("papers.findings.items", { count: finding.record_count })}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <SectionTitle
            title={t("papers.evidence.title")}
            description={t("papers.evidence.desc")}
            className="mt-8"
          />
          <div className="space-y-3">
            {auditData.graph.nodes.length > 0 ? (
              auditData.graph.nodes.map((node) => (
                <div key={node.node_id} className="rounded-lg border border-gray-100 px-4 py-3 bg-white">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs text-gray-400">
                      {node.node_id}
                    </span>
                    <span className="rounded-md bg-gray-50 px-2 py-1 text-[11px] font-medium text-gray-500">
                      {node.node_type}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-gray-600">
                    {node.content}
                  </p>
                </div>
              ))
            ) : (
              <p className="rounded-lg border border-gray-100 px-4 py-3 text-sm text-gray-400 bg-white">
                {t("papers.evidence.empty")}
              </p>
            )}
          </div>
        </section>

        <section>
          <SectionTitle title={t("papers.preview.title")} description={t("papers.preview.desc")} />
          <pre className="max-h-[680px] whitespace-pre-wrap break-words overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-5 text-xs leading-6 text-gray-700 font-mono">
            {workingPaper}
          </pre>
        </section>
      </main>
    </div>
  );
}

function EmptyPapers() {
  const { t } = useTranslation();
  return (
    <StateMessage
      icon={Upload}
      title={t("papers.empty.title")}
      description={t("papers.empty.desc")}
      actionLabel={t("papers.empty.btn")}
      actionHref="/"
    />
  );
}

function StateMessage({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
}: {
  icon: typeof FileText;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}) {
  const { t } = useTranslation();
  const actionClass =
    "mt-7 inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 cursor-pointer";

  return (
    <div className="animate-fade-in stagger-1">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          {t("papers.back")}
        </Link>
      </div>
      <div className="flex min-h-[56vh] flex-col items-center justify-center text-center">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-lg bg-gray-50">
          <Icon size={23} className="text-gray-500" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-gray-950">
          {title}
        </h1>
        <p className="mt-3 max-w-md text-sm leading-6 text-gray-400">
          {description}
        </p>
        {actionHref && actionLabel && (
          <Link href={actionHref} className={actionClass}>
            {actionLabel}
            <ArrowRight size={15} />
          </Link>
        )}
        {onAction && actionLabel && (
          <button type="button" onClick={onAction} className={actionClass}>
            {actionLabel}
            <RefreshCw size={15} />
          </button>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border-l border-gray-100 pl-3">
      <p className="text-[11px] font-medium text-gray-400">{label}</p>
      <p className="mt-1 break-words text-lg font-semibold tracking-tight text-gray-950">
        {value}
      </p>
    </div>
  );
}

function SectionTitle({
  title,
  description,
  className = "",
}: {
  title: string;
  description: string;
  className?: string;
}) {
  return (
    <div className={`mb-4 flex items-start gap-2.5 ${className}`}>
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gray-50">
        <CheckCircle2 size={15} className="text-gray-500" />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-gray-950">{title}</h2>
        <p className="mt-1 text-xs leading-5 text-gray-400">{description}</p>
      </div>
    </div>
  );
}
