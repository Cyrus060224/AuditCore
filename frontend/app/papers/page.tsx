"use client";

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
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

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

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getRiskLabel(data: AuditData) {
  if (data.stats.anomaly_count >= 5) return "高风险";
  if (data.stats.anomaly_count > 0) return "中风险";
  return "低风险";
}

function buildWorkingPaper(session: UploadedAuditSession) {
  const { auditData, fileName, uploadedAt } = session;
  const findings = auditData.rule_findings;
  const activeFindings = findings.filter((finding) => finding.record_count > 0);
  const maxAmount =
    auditData.stats.max_amount == null
      ? "未识别"
      : `¥${auditData.stats.max_amount.toLocaleString()}`;

  const findingLines =
    findings.length > 0
      ? findings
          .map(
            (finding) =>
              `- ${finding.label}: ${finding.record_count} 条；${finding.summary}`
          )
          .join("\n")
      : "- 未生成规则发现。";

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
          .join("\n") || "- 当前无异常证据节点。";

  const conclusion =
    auditData.stats.anomaly_count > 0
      ? "本次规则扫描发现异常记录，建议进入多 Agent 复核和凭证补证流程。"
      : "本次规则扫描未发现异常记录，建议按常规流程归档，并保留抽样记录。";

  return `# 审计工作底稿

## 1. 审计对象
- 文件名称: ${fileName}
- 上传时间: ${formatDateTime(uploadedAt)}
- 数据来源: AuditCore Excel 上传审计

## 2. 扫描概览
- 总记录数: ${auditData.stats.total_records}
- 异常记录数: ${auditData.stats.anomaly_count}
- 最大金额: ${maxAmount}
- 全局一致性评分: ${auditData.global_consistency_score.toFixed(2)}
- 风险等级: ${getRiskLabel(auditData)}

## 3. 规则发现
${findingLines}

## 4. 证据节点
${evidenceLines}

## 5. 审计结论
${conclusion}

## 6. 下一步动作
${
  auditData.stats.anomaly_count > 0
    ? "- 调取原始凭证、审批流和业务说明。\n- 将异常规则发现提交虚拟审计组进行质证和仲裁。\n- 对高金额或重复记录形成专项底稿附件。"
    : "- 保存本次扫描记录。\n- 确认数据覆盖期间和字段映射完整性。\n- 按常规审计归档流程处理。"
}
`;
}

export default function WorkingPapers() {
  const [session, setSession] = useState<UploadedAuditSession | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [copyStatus, setCopyStatus] = useState("复制底稿");

  const workingPaper = useMemo(
    () => (session ? buildWorkingPaper(session) : ""),
    [session]
  );

  async function loadLatestAudit() {
    setLoadState("loading");
    setCopyStatus("复制底稿");

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
      setCopyStatus("已复制");
    } catch {
      setCopyStatus("复制失败");
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
        title="无法连接后端"
        description={`请确认 AuditCore API 已在 ${API_BASE_URL} 启动，然后重新加载底稿。`}
        actionLabel="重新加载"
        onAction={loadLatestAudit}
      />
    );
  }

  if (loadState === "loading" || !session) {
    return (
      <StateMessage
        icon={RefreshCw}
        title="正在读取最新审计结果"
        description="系统正在从后端获取最近一次上传文件的扫描结果。"
      />
    );
  }

  const auditData = session.auditData;
  const riskLabel = getRiskLabel(auditData);

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
            <FileText size={13} />
            审计工作底稿
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-950">
            {session.fileName}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-500">
            基于最近一次上传文件自动生成底稿摘要，包含扫描概览、规则发现、证据节点和下一步审计动作。
          </p>
          <p className="mt-2 text-xs text-gray-400">
            上传时间：{formatDateTime(session.uploadedAt)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={loadLatestAudit}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50"
          >
            <RefreshCw size={15} />
            刷新
          </button>
          <button
            type="button"
            onClick={copyWorkingPaper}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50"
          >
            <Clipboard size={15} />
            {copyStatus}
          </button>
          <button
            type="button"
            onClick={downloadWorkingPaper}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-gray-950 px-3.5 text-sm font-medium text-white transition-colors hover:bg-gray-800"
          >
            <Download size={15} />
            下载 Markdown
          </button>
        </div>
      </header>

      <div className="mb-8 grid gap-6 sm:grid-cols-4">
        <Metric label="总记录数" value={String(auditData.stats.total_records)} />
        <Metric label="异常记录" value={String(auditData.stats.anomaly_count)} />
        <Metric
          label="最大金额"
          value={
            auditData.stats.max_amount == null
              ? "未识别"
              : `¥${auditData.stats.max_amount.toLocaleString()}`
          }
        />
        <Metric label="风险等级" value={riskLabel} />
      </div>

      <main className="grid gap-8 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <section>
          <SectionTitle title="规则发现" description="来自当前上传文件的实时规则扫描结果。" />
          <div className="space-y-3">
            {auditData.rule_findings.map((finding) => (
              <div key={finding.label} className="rounded-lg border border-gray-100 px-4 py-3">
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
                    {finding.record_count} 条
                  </span>
                </div>
              </div>
            ))}
          </div>

          <SectionTitle
            title="证据节点"
            description="底稿中保留的规则事实节点，后续可连接多 Agent 质证关系。"
            className="mt-8"
          />
          <div className="space-y-3">
            {auditData.graph.nodes.length > 0 ? (
              auditData.graph.nodes.map((node) => (
                <div key={node.node_id} className="rounded-lg border border-gray-100 px-4 py-3">
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
              <p className="rounded-lg border border-gray-100 px-4 py-3 text-sm text-gray-400">
                当前扫描没有生成证据节点。
              </p>
            )}
          </div>
        </section>

        <section>
          <SectionTitle title="Markdown 底稿预览" description="可直接复制或下载，用作专利演示和审计归档材料。" />
          <pre className="max-h-[680px] whitespace-pre-wrap break-words overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-5 text-xs leading-6 text-gray-700">
            {workingPaper}
          </pre>
        </section>
      </main>
    </div>
  );
}

function EmptyPapers() {
  return (
    <StateMessage
      icon={Upload}
      title="请先上传审计文件"
      description="工作底稿页会读取最近一次 Excel 上传结果，并自动生成可复制、可下载的 Markdown 底稿。"
      actionLabel="返回上传"
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
  const actionClass =
    "mt-7 inline-flex h-10 items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50";

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
