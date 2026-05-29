"use client";

import { useEffect, useState, useCallback } from "react";
import { ArrowLeft, Settings, Save, CheckCircle2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useTranslation } from "../i18n";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_AUDIT_API_BASE_URL ?? "http://127.0.0.1:8000";

const PROVIDER_LIST = [
  "ollama", "openai", "deepseek", "qwen", "moonshot", "siliconflow", "anthropic",
] as const;

type ProviderId = typeof PROVIDER_LIST[number];

interface LLMConfigForm {
  provider: ProviderId;
  api_key: string;
  base_url: string;
  model: string;
}

interface ModelData {
  config: Record<string, { provider: string; model: string; base_url: string; api_key: string }>;
  providerPresets: Record<string, { base_url: string; model: string }>;
}

const AGENT_IDS = ["junior", "challenger", "factcheck", "senior"] as const;

const AGENT_LABELS_ZH: Record<string, string> = {
  junior: "初级审计",
  challenger: "挑战者",
  factcheck: "事实核查",
  senior: "高级合伙人",
};

const AGENT_LABELS_EN: Record<string, string> = {
  junior: "Junior Auditor",
  challenger: "Challenger",
  factcheck: "Fact Checker",
  senior: "Senior Partner",
};

function getDefaultForm(presets: Record<string, { base_url: string; model: string }>): LLMConfigForm {
  const p = presets?.ollama ?? { base_url: "http://localhost:11434/v1", model: "llama3:8b" };
  return { provider: "ollama", api_key: "", base_url: p.base_url, model: p.model };
}

function parseConfig(
  data: ModelData,
  presets: Record<string, { base_url: string; model: string }>,
): { default: LLMConfigForm; agents: Record<string, LLMConfigForm> } {
  const dc = data.config?.default ?? {};
  const defaultForm: LLMConfigForm = {
    provider: (dc.provider as ProviderId) || "ollama",
    api_key: dc.api_key === "***" ? "" : (dc.api_key ?? ""),
    base_url: dc.base_url ?? presets?.ollama?.base_url ?? "",
    model: dc.model ?? presets?.ollama?.model ?? "",
  };

  const agents: Record<string, LLMConfigForm> = {};
  for (const aid of AGENT_IDS) {
    const ac = data.config?.[aid];
    if (ac) {
      agents[aid] = {
        provider: (ac.provider as ProviderId) || defaultForm.provider,
        api_key: ac.api_key === "***" ? "" : (ac.api_key ?? ""),
        base_url: ac.base_url ?? "",
        model: ac.model ?? "",
      };
    }
  }

  return { default: defaultForm, agents };
}

/* ─── Provider Pill 按钮组 ─── */

function ProviderPills({
  value,
  onChange,
}: {
  value: ProviderId;
  onChange: (p: ProviderId) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {PROVIDER_LIST.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onChange(p)}
          className={`rounded-md px-2.5 py-1 text-[12px] font-medium transition-all duration-150 cursor-pointer ${
            value === p
              ? "bg-gray-900 text-white shadow-xs"
              : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
          }`}
        >
          {p}
        </button>
      ))}
    </div>
  );
}

/* ─── 配置表单区块 ─── */

function ConfigSection({
  title,
  desc,
  form,
  presets,
  onChange,
  labelMap,
}: {
  title: string;
  desc?: string;
  form: LLMConfigForm;
  presets: Record<string, { base_url: string; model: string }>;
  onChange: (f: LLMConfigForm) => void;
  labelMap?: Record<string, string>;
}) {
  const { t } = useTranslation();

  const handleProviderChange = (p: ProviderId) => {
    const preset = presets?.[p] ?? { base_url: "", model: "" };
    onChange({
      ...form,
      provider: p,
      base_url: preset.base_url,
      model: preset.model,
    });
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      {desc && <p className="mt-1 text-xs text-gray-400">{desc}</p>}

      <div className="mt-4 space-y-4">
        {/* Provider */}
        <div>
          <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-gray-400">
            {t("settings.provider")}
          </label>
          <ProviderPills value={form.provider} onChange={handleProviderChange} />
        </div>

        {/* API Key */}
        <div>
          <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-gray-400">
            {t("settings.apiKey")}
          </label>
          <input
            type="password"
            value={form.api_key}
            onChange={(e) => onChange({ ...form, api_key: e.target.value })}
            placeholder={t("settings.apiKeyPlaceholder")}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-300 focus:border-gray-400 focus:outline-none focus:ring-0"
          />
        </div>

        {/* Base URL */}
        <div>
          <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-gray-400">
            {t("settings.baseUrl")}
          </label>
          <input
            type="text"
            value={form.base_url}
            onChange={(e) => onChange({ ...form, base_url: e.target.value })}
            placeholder={t("settings.baseUrlPlaceholder")}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-300 focus:border-gray-400 focus:outline-none focus:ring-0"
          />
        </div>

        {/* Model */}
        <div>
          <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-gray-400">
            {t("settings.model")}
          </label>
          <input
            type="text"
            value={form.model}
            onChange={(e) => onChange({ ...form, model: e.target.value })}
            placeholder={t("settings.modelPlaceholder")}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-300 focus:border-gray-400 focus:outline-none focus:ring-0"
          />
        </div>
      </div>
    </div>
  );
}

/* ─── 主页面 ─── */

export default function SettingsPage() {
  const { t, locale } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);
  const [presets, setPresets] = useState<Record<string, { base_url: string; model: string }>>({});
  const [defaultForm, setDefaultForm] = useState<LLMConfigForm>({
    provider: "ollama", api_key: "", base_url: "", model: "",
  });
  const [agentForms, setAgentForms] = useState<Record<string, LLMConfigForm>>({});
  const [agentEnabled, setAgentEnabled] = useState<Record<string, boolean>>({});

  const agentLabels = locale === "zh" ? AGENT_LABELS_ZH : AGENT_LABELS_EN;

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/models`);
        const data: ModelData = await res.json();
        const p = data.providerPresets ?? {};
        setPresets(p);
        const parsed = parseConfig(data, p);
        setDefaultForm(parsed.default);
        setAgentForms(parsed.agents);
        const enabled: Record<string, boolean> = {};
        for (const aid of AGENT_IDS) {
          enabled[aid] = !!parsed.agents[aid];
        }
        setAgentEnabled(enabled);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setToast(null);
    try {
      const agents: Record<string, LLMConfigForm> = {};
      for (const aid of AGENT_IDS) {
        if (agentEnabled[aid] && agentForms[aid]) {
          agents[aid] = agentForms[aid];
        }
      }
      const res = await fetch(`${API_BASE_URL}/api/models`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ default: defaultForm, agents }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setToast({ type: "ok", msg: t("settings.saved") });
    } catch {
      setToast({ type: "err", msg: t("settings.saveFailed") });
    } finally {
      setSaving(false);
      setTimeout(() => setToast(null), 3000);
    }
  }, [defaultForm, agentForms, agentEnabled, t]);

  const setAgentForm = (aid: string, form: LLMConfigForm) => {
    setAgentForms((prev) => ({ ...prev, [aid]: form }));
  };

  if (loading) {
    return (
      <div className="animate-fade-in stagger-1">
        <div className="flex min-h-[40vh] items-center justify-center">
          <p className="text-sm text-gray-400">{t("settings.saving")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in stagger-1">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <Link href="/" className="mb-3 inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700">
            <ArrowLeft size={14} />
            {t("settings.back")}
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">{t("settings.title")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-400">{t("settings.subtitle")}</p>
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="inline-flex h-10 items-center gap-2 rounded-lg bg-gray-900 px-4 text-sm font-medium text-white transition-colors hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
        >
          <Save size={15} />
          {saving ? t("settings.saving") : t("settings.save")}
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`mb-6 flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm ${
          toast.type === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
        }`}>
          {toast.type === "ok" ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
          {toast.msg}
        </div>
      )}

      {/* Default config */}
      <ConfigSection
        title={t("settings.defaultTitle")}
        desc={t("settings.defaultDesc")}
        form={defaultForm}
        presets={presets}
        onChange={setDefaultForm}
      />

      {/* Per-agent overrides */}
      <div className="mt-8">
        <h2 className="text-sm font-semibold text-gray-900">{t("settings.agentOverride")}</h2>
        <p className="mt-1 text-xs text-gray-400">{t("settings.agentOverrideDesc")}</p>

        <div className="mt-4 space-y-4">
          {AGENT_IDS.map((aid) => (
            <div key={aid} className="rounded-xl border border-gray-200 bg-white">
              <button
                type="button"
                onClick={() => setAgentEnabled((prev) => ({ ...prev, [aid]: !prev[aid] }))}
                className="flex w-full items-center justify-between px-5 py-3.5 cursor-pointer"
              >
                <span className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={agentEnabled[aid] ?? false}
                    readOnly
                    className="h-4 w-4 rounded border-gray-300 accent-gray-900"
                  />
                  <span className="text-sm font-medium text-gray-900">
                    {agentLabels[aid] ?? aid}
                  </span>
                </span>
                <span className="text-xs text-gray-400">
                  {agentEnabled[aid]
                    ? `${agentForms[aid]?.provider ?? "—"} · ${agentForms[aid]?.model || t("settings.custom")}`
                    : "—"
                  }
                </span>
              </button>

              {agentEnabled[aid] && (
                <div className="border-t border-gray-100 px-5 pb-5 pt-4">
                  <ConfigSection
                    title={agentLabels[aid] ?? aid}
                    form={agentForms[aid] ?? getDefaultForm(presets)}
                    presets={presets}
                    onChange={(f) => setAgentForm(aid, f)}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
