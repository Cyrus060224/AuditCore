import { BarChart3, Bot, GitBranch, Settings2 } from "lucide-react";

const navItems = [
  { label: "审计总控台", icon: BarChart3, active: true },
  { label: "智能体博弈", icon: Bot, active: false },
  { label: "图谱控制室", icon: GitBranch, active: false },
  { label: "系统设置", icon: Settings2, active: false },
];

export function Sidebar() {
  return (
    <aside className="sticky top-0 h-screen w-64 shrink-0 border-r border-slate-200 bg-white px-5 py-6">
      <div className="mb-10">
        <div className="text-xl font-semibold tracking-tight text-slate-950">
          ⚡ AuditCore
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          Multi-Agent Audit Control Plane
        </p>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <a
              className={[
                "flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
                item.active
                  ? "bg-slate-100 text-slate-950"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900",
              ].join(" ")}
              href="#"
              key={item.label}
            >
              <Icon className="h-4 w-4" strokeWidth={2} />
              {item.label}
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
