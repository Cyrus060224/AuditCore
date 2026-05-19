import { Activity, AlertTriangle, CheckCircle2, Database } from "lucide-react";

const metrics = [
  {
    label: "全局一致性评分",
    value: "0.85",
    caption: "Evidence graph consensus",
    icon: Activity,
  },
  {
    label: "扫描记录数",
    value: "10",
    caption: "Transactions processed",
    icon: Database,
  },
  {
    label: "初审异常数",
    value: "3",
    caption: "Rule findings detected",
    icon: AlertTriangle,
  },
  {
    label: "涉案总金额",
    value: "¥2.4M",
    caption: "Amount under review",
    icon: CheckCircle2,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen flex-1 px-6 py-6 lg:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-medium text-slate-500">AuditCore SaaS</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              审计总控台
            </h1>
          </div>
          <div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm">
            STATE_FINAL_VERDICT
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon;

            return (
              <article
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
                key={metric.label}
              >
                <div className="mb-6 flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-500">
                    {metric.label}
                  </p>
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-600">
                    <Icon className="h-4 w-4" strokeWidth={2} />
                  </div>
                </div>
                <div className="text-4xl font-extrabold tracking-tight text-slate-950">
                  {metric.value}
                </div>
                <p className="mt-3 text-sm text-slate-500">{metric.caption}</p>
              </article>
            );
          })}
        </section>

        <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 shadow-sm">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
            <div>
              <h2 className="text-base font-semibold">穿透审计通过</h2>
              <p className="mt-1 text-sm text-emerald-700">
                数据一致性达标，状态机已推进至最终合伙人裁决阶段。
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-center">
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-slate-950">
                数据与仲裁记录
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                未来用于承载 DataFrame 表格、图谱节点与深度仲裁日志。
              </p>
            </div>
            <span className="w-fit rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
              Mock Data
            </span>
          </div>

          <div className="mt-6 grid min-h-80 place-items-center rounded-lg border border-dashed border-slate-300 bg-slate-50">
            <div className="text-center">
              <Database className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-3 text-sm font-medium text-slate-700">
                等待接入后端审计数据流
              </p>
              <p className="mt-1 text-sm text-slate-500">
                TransactionID、异常凭证、证据边将在这里集中展示。
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
