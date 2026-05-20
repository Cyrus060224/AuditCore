"use client";

import {
  Target,
  ScrollText,
  AlertTriangle,
  Banknote,
  CheckCircle2,
  Upload,
  Loader2,
  FileSpreadsheet,
  AlertCircle,
} from "lucide-react";
import { useState, useCallback } from "react";

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
  global_consistency_score: 0.85,
  current_state: "STATE_FINAL_VERDICT",
  consistency_threshold: 0.8,
  stats: {
    total_records: 10,
    anomaly_count: 3,
    max_amount: 49999,
  },
  rule_findings: [
    { label: "Negative Amounts", record_count: 2, summary: "Negative Amounts: 2 record(s)" },
    { label: "Duplicate Rows", record_count: 1, summary: "Duplicate Rows: 1 record(s)" },
  ],
  graph: {
    nodes: [
      { node_id: "rule_fact_0", node_type: "RuleFinding", content: "Negative Amounts: 2 record(s)" },
      { node_id: "rule_fact_1", node_type: "RuleFinding", content: "Duplicate Rows: 1 record(s)" },
    ],
    edges: [],
  },
};

const METRICS = [
  { label: "全局一致性评分", key: "score" as const, icon: Target },
  { label: "扫描记录", key: "records" as const, icon: ScrollText },
  { label: "硬事实异常", key: "anomalies" as const, icon: AlertTriangle },
  { label: "涉案金额", key: "amount" as const, icon: Banknote },
];

export default function Dashboard() {
  const [auditData, setAuditData] = useState<AuditData>(MOCK_DATA);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileUpload = useCallback(async (file: File) => {
    console.log("[AuditCore] File selected:", file.name, file.size);

    if (!file.name.endsWith(".xlsx")) {
      console.warn("[AuditCore] Rejected non-xlsx file:", file.name);
      setError("Only .xlsx files are accepted");
      return;
    }

    console.log("[AuditCore] Upload started", { name: file.name, size: file.size });
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      alert("开始上传并分析，请稍候...");

      console.log("[AuditCore] Sending POST to http://localhost:8000/api/audit ...");
      const response = await fetch("http://localhost:8000/api/audit", {
        method: "POST",
        body: formData,
      });

      console.log("[AuditCore] Response status:", response.status);

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const data: AuditData = await response.json();
      console.log("[AuditCore] Upload success, audit data:", data);
      setAuditData(data);
      alert("分析成功！");
    } catch (err) {
      console.error("[AuditCore] Upload failed:", err);
      const msg = err instanceof Error ? err.message : "Upload failed";
      setError(msg);
      setAuditData(MOCK_DATA);
      alert("上传失败: " + msg);
    } finally {
      console.log("[AuditCore] Upload flow completed");
      setUploading(false);
    }
  }, []);

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

  const metricValues: Record<string, string> = {
    score: score.toFixed(2),
    records: String(totalRecords),
    anomalies: String(anomalyCount),
    amount: maxAmount != null ? `¥${maxAmount.toLocaleString()}` : "N/A",
  };

  const metricTrends: Record<string, string> = {
    score: `${score >= 0.8 ? "✅" : "⚠️"} 阈值 ${auditData.consistency_threshold}`,
    records: "已处理记录",
    anomalies: anomalyCount > 0 ? "待处理" : "无异常",
    amount: maxAmount != null && maxAmount > 0 ? `${auditData.rule_findings.length} 类规则发现` : "无涉案金额",
  };

  const isVerdict = auditData.current_state === "STATE_FINAL_VERDICT";

  return (
    <div className="space-y-8 p-8">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            审计总控台
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            穿透式审计智能体协作平台 · 实时监控中心
          </p>
        </div>
      </header>

      <section className="rounded-xl border border-dashed border-slate-300 bg-white p-6 transition-colors hover:border-slate-400">
        <div
          className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-8 transition-all ${
            dragging
              ? "border-indigo-400 bg-indigo-50"
              : "border-slate-200 bg-slate-50/50"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <Upload
            size={24}
            className={`${uploading ? "text-indigo-500" : "text-slate-400"}`}
          />
          <div className="text-center">
            <label
              htmlFor="file-upload"
              className="cursor-pointer text-sm font-medium text-slate-700 hover:text-slate-900"
            >
              {uploading ? "正在解析..." : "点击上传或拖拽 .xlsx 文件"}
            </label>
            <p className="mt-1 text-xs text-slate-400">
              支持 Excel 审计数据文件
            </p>
          </div>
          <input
            id="file-upload"
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={handleChange}
            disabled={uploading}
          />
          {uploading && (
            <Loader2 size={18} className="animate-spin text-indigo-500" />
          )}
        </div>
      </section>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-6 py-4">
          <AlertCircle size={18} className="shrink-0 text-red-500" />
          <span className="text-sm font-medium text-red-700">{error}</span>
        </div>
      )}

      <section className="grid grid-cols-4 gap-6">
        {METRICS.map((metric) => {
          const Icon = metric.icon;
          return (
            <div
              key={metric.label}
              className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                <Icon size={16} strokeWidth={1.75} />
                {metric.label}
              </div>
              <div className="text-4xl font-extrabold tracking-tight text-slate-900">
                {metricValues[metric.key]}
              </div>
              <div className="text-xs text-slate-400">
                {metricTrends[metric.key]}
              </div>
            </div>
          );
        })}
      </section>

      <section>
        {isVerdict ? (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-6 py-4">
            <CheckCircle2 size={20} className="shrink-0 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-700">
              穿透审计通过：状态机已安全推进至合伙人裁决阶段
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-6 py-4">
            <AlertCircle size={20} className="shrink-0 text-red-600" />
            <span className="text-sm font-medium text-red-700">
              专利熔断机制触发：一致性评分 {score.toFixed(2)} 低于阈值{" "}
              {auditData.consistency_threshold}，状态机回退至复核阶段
            </span>
          </div>
        )}
      </section>

      <section>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-100 px-6 py-4">
            <FileSpreadsheet size={16} className="text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-700">
              原始凭证记录
            </h2>
          </div>

          {auditData.rule_findings.length > 0 ? (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50 text-xs font-medium uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-3">规则标签</th>
                  <th className="px-6 py-3">异常条数</th>
                  <th className="px-6 py-3">摘要</th>
                  <th className="px-6 py-3 text-right">严重度</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {auditData.rule_findings.map((finding, i) => (
                  <tr
                    key={i}
                    className="transition-colors hover:bg-slate-50"
                  >
                    <td className="px-6 py-3 font-mono text-xs text-slate-500">
                      {finding.label}
                    </td>
                    <td className="px-6 py-3 font-medium text-slate-900">
                      {finding.record_count}
                    </td>
                    <td className="px-6 py-3 text-slate-600">
                      {finding.summary}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <StatusBadge
                        status={
                          finding.record_count >= 2 ? "高风险" : "低风险"
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <FileSpreadsheet
                size={32}
                className="mb-3 text-slate-300"
              />
              <p className="text-sm text-slate-400">
                暂无规则发现，请上传审计数据文件
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const style =
    status === "高风险"
      ? "bg-red-50 text-red-700"
      : "bg-emerald-50 text-emerald-700";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {status}
    </span>
  );
}