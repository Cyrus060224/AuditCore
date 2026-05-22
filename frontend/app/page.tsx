"use client";

import {
  CheckCircle2,
  Upload,
  AlertCircle,
  Clock,
  X,
  Bot,
  ArrowRight,
  Server,
} from "lucide-react";
import Link from "next/link";
import { useState, useCallback, useEffect } from "react";
import { useTranslation } from "./i18n";

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

const MOCK_DATA: AuditData = {
  global_consistency_score: 0,
  current_state: "STATE_INITIAL",
  consistency_threshold: 0.8,
  stats: {
    total_records: 0,
    anomaly_count: 0,
    max_amount: null,
  },
  rule_findings: [],
  graph: {
    nodes: [],
    edges: [],
  },
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_AUDIT_API_BASE_URL ?? "http://127.0.0.1:8000";
const LATEST_AUDIT_STORAGE_KEY = "auditcore.latestAuditRun";

type ApiStatus = "checking" | "online" | "offline";

export default function Dashboard() {
  const { t } = useTranslation();
  const [auditData, setAuditData] = useState<AuditData>(MOCK_DATA);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  const checkApiStatus = useCallback(async () => {
    setApiStatus("checking");
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        method: "GET",
      });
      setApiStatus(response.ok ? "online" : "offline");
    } catch {
      setApiStatus("offline");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadApiStatus() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/health`, {
          method: "GET",
        });
        if (!cancelled) {
          setApiStatus(response.ok ? "online" : "offline");
        }
      } catch {
        if (!cancelled) {
          setApiStatus("offline");
        }
      }
    }

    loadApiStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleFileUpload = useCallback(async (file: File) => {
    if (!file.name.endsWith(".xlsx")) {
      setError(t("console.upload.formatError"));
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/api/audit`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`审计接口返回异常状态：${response.status}`);
      }

      const data: AuditData = await response.json();
      if ("error" in data) {
        throw new Error(String(data.error));
      }
      setAuditData(data);
      window.localStorage.setItem(
        LATEST_AUDIT_STORAGE_KEY,
        JSON.stringify({
          fileName: file.name,
          uploadedAt: new Date().toISOString(),
          auditData: data,
        })
      );
      setApiStatus("online");
    } catch (err) {
      const msg =
        err instanceof TypeError
          ? t("console.upload.backendError", { url: API_BASE_URL })
          : err instanceof Error
          ? err.message
          : t("console.upload.genericError");
      setError(msg);
      checkApiStatus();
      setAuditData(MOCK_DATA);
    } finally {
      setIsAnalyzing(false);
    }
  }, [checkApiStatus, t]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload]
  );

  const score = auditData.global_consistency_score;
  const totalRecords = auditData.stats.total_records;
  const anomalyCount = auditData.stats.anomaly_count;
  const maxAmount = auditData.stats.max_amount;

  const isVerdict = auditData.current_state === "STATE_FINAL_VERDICT";
  const hasData = totalRecords > 0;

  return (
    <div>
      {/* Page title */}
      <div className="mb-12 flex flex-col gap-5 animate-fade-in stagger-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-905">
            {t("console.title")}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-400">
            {t("console.subtitle")}
          </p>
          <ApiStatusLine status={apiStatus} onRefresh={checkApiStatus} />
        </div>
        <Link
          href="/arena"
          className="inline-flex h-10 w-fit items-center gap-2 rounded-lg border border-gray-200 px-3.5 text-sm font-medium text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 cursor-pointer"
        >
          <Bot size={16} />
          {t("console.arenaBtn")}
          <ArrowRight size={15} />
        </Link>
      </div>

      {/* Metrics row */}
      {hasData && (
        <div className="mb-8 animate-fade-in stagger-2">
          <div className="grid grid-cols-4 gap-8">
            <MetricValue
              label={t("console.metrics.consistency")}
              value={score.toFixed(2)}
              status={score >= 0.8 ? "good" : "warning"}
              delay={1}
            />
            <MetricValue
              label={t("console.metrics.scanned")}
              value={String(totalRecords)}
              subtitle={t("console.metrics.records")}
              delay={2}
            />
            <MetricValue
              label={t("console.metrics.anomalies")}
              value={String(anomalyCount)}
              status={anomalyCount > 0 ? "warning" : "good"}
              delay={3}
            />
            <MetricValue
              label={t("console.metrics.exposure")}
              value={maxAmount != null ? `¥${maxAmount.toLocaleString()}` : "—"}
              delay={4}
            />
          </div>
        </div>
      )}

      {/* Verdict banner */}
      {hasData && (
        <div className="mb-8 animate-fade-in stagger-3">
          <Verdict isVerdict={isVerdict} score={score} threshold={auditData.consistency_threshold} />
        </div>
      )}

      {/* Upload section */}
      <div className="animate-fade-in stagger-4">
        <UploadSection
          isAnalyzing={isAnalyzing}
          error={error}
          dragging={dragging}
          apiStatus={apiStatus}
          onDrop={handleDrop}
          onChange={handleChange}
          onDragOver={(e: React.DragEvent) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
        />
      </div>

      {/* Data table */}
      {hasData && (
        <div className="mt-8 animate-fade-in stagger-5">
          <DataTable findings={auditData.rule_findings} />
        </div>
      )}
    </div>
  );
}

/* ─── Metric ── */

function MetricValue({
  label,
  value,
  subtitle,
  status,
  delay,
}: {
  label: string;
  value: string;
  subtitle?: string;
  status?: "good" | "warning";
  delay: number;
}) {
  const dotColor =
    status === "good"
      ? "bg-emerald-500"
      : status === "warning"
      ? "bg-amber-500"
      : "bg-gray-200";

  return (
    <div className={`animate-fade-in stagger-${delay}`}>
      <div className="flex items-center gap-2">
        <div className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
        <span className="text-[11px] font-medium uppercase tracking-wider text-gray-400">
          {label}
        </span>
      </div>
      <div className="mt-1.5 text-3xl font-semibold tracking-tight text-gray-900">
        {value}
      </div>
      {subtitle && (
        <p className="mt-0.5 text-xs text-gray-400">{subtitle}</p>
      )}
    </div>
  );
}

/* ─── API Status ─── */

function ApiStatusLine({
  status,
  onRefresh,
}: {
  status: ApiStatus;
  onRefresh: () => void;
}) {
  const { t } = useTranslation();
  const statusText =
    status === "online"
      ? t("console.api.connected")
      : status === "checking"
      ? t("console.api.checking")
      : t("console.api.disconnected");
  const dotColor =
    status === "online"
      ? "bg-emerald-500"
      : status === "checking"
      ? "bg-blue-500"
      : "bg-red-500";

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-gray-400">
      <span className="inline-flex items-center gap-1.5">
        <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
        <Server size={13} />
        {statusText}
      </span>
      <span className="font-mono text-[11px]">{API_BASE_URL}</span>
      <button
        type="button"
        onClick={onRefresh}
        className="rounded-md px-1.5 py-0.5 font-medium text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-800 cursor-pointer"
      >
        {t("console.api.recheck")}
      </button>
    </div>
  );
}

/* ─── Verdict ─── */

function Verdict({
  isVerdict,
  score,
  threshold,
}: {
  isVerdict: boolean;
  score: number;
  threshold: number;
}) {
  const { t } = useTranslation();
  if (isVerdict) {
    return (
      <div className="flex items-center gap-2.5">
        <CheckCircle2 size={15} className="text-emerald-500" />
        <span className="text-sm text-gray-700">
          {t("console.verdict.passed")}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5">
      <AlertCircle size={15} className="mt-0.5 text-red-500" />
      <div>
        <p className="text-sm font-medium text-red-600">
          {t("console.verdict.failed", { score: score.toFixed(2) })}
        </p>
        <p className="mt-0.5 text-xs text-red-400">
          {t("console.verdict.regressed", { threshold })}
        </p>
      </div>
    </div>
  );
}

/* ─── Upload ─── */

function UploadSection({
  isAnalyzing,
  error,
  dragging,
  apiStatus,
  onDrop,
  onChange,
  onDragOver,
  onDragLeave,
}: {
  isAnalyzing: boolean;
  error: string | null;
  dragging: boolean;
  apiStatus: ApiStatus;
  onDrop: (e: React.DragEvent) => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div>
      <div
        className={`flex cursor-pointer items-center justify-between rounded-xl border px-5 py-4 transition-colors ${
          dragging
            ? "border-gray-300 bg-gray-50"
            : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => {
          if (!isAnalyzing) {
            document.getElementById("file-upload")?.click();
          }
        }}
      >
        <div className="flex items-center gap-4">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
              isAnalyzing
                ? "bg-blue-50"
                : dragging
                ? "bg-gray-100"
                : "bg-gray-50"
            }`}
          >
            {isAnalyzing ? (
              <Clock size={17} className="animate-spin text-blue-500" />
            ) : apiStatus === "offline" ? (
              <AlertCircle size={17} className="text-red-500" />
            ) : (
              <Upload size={17} className="text-gray-500" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {isAnalyzing ? t("console.upload.analyzing") : t("console.upload.uploadXlsx")}
            </p>
            {!isAnalyzing && (
              <p className="text-xs text-gray-400">
                {apiStatus === "offline"
                  ? t("console.upload.offlineTip")
                  : t("console.upload.dragTip")}
              </p>
            )}
          </div>
        </div>

        <input
          id="file-upload"
          type="file"
          accept=".xlsx"
          className="hidden"
          onChange={onChange}
          disabled={isAnalyzing}
        />
      </div>

      {error && (
        <div className="mt-2 flex items-center gap-1.5">
          <X size={12} className="text-red-500" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}
    </div>
  );
}

/* ─── Table ─── */

function DataTable({
  findings,
}: {
  findings: Array<{
    label: string;
    record_count: number;
    summary: string;
  }>;
}) {
  const { t } = useTranslation();
  if (findings.length === 0) return null;

  return (
    <div>
      <p className="mb-4 text-[11px] font-medium uppercase tracking-wider text-gray-400">
        {t("console.table.findings", { count: findings.length })}
      </p>
      <div className="overflow-hidden rounded-xl border border-gray-100 bg-white">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-[11px] font-medium uppercase tracking-wider text-gray-400">
              <th className="px-5 py-3">{t("console.table.rule")}</th>
              <th className="px-5 py-3">{t("console.table.records")}</th>
              <th className="px-5 py-3">{t("console.table.summary")}</th>
              <th className="px-5 py-3 text-right">{t("console.table.severity")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {findings.map((f, i) => (
              <tr key={i} className="text-sm text-gray-900">
                <td className="px-5 py-3 font-mono text-xs text-gray-500">
                  {f.label}
                </td>
                <td className="px-5 py-3 font-medium">
                  {f.record_count}
                </td>
                <td className="px-5 py-3 text-gray-500">
                  {f.summary}
                </td>
                <td className="px-5 py-3 text-right">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs ${
                      f.record_count >= 2
                        ? "bg-red-50 text-red-600"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    <div
                      className={`h-1 w-1 rounded-full ${
                        f.record_count >= 2
                          ? "bg-red-500"
                          : "bg-gray-400"
                      }`}
                    />
                    {f.record_count >= 2 ? t("console.table.high") : t("console.table.low")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

