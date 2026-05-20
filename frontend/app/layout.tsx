import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { LayoutDashboard, Bot, FileText } from "lucide-react";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AuditCore — 穿透式审计智能平台",
  description: "企业级穿透式审计智能体协作平台",
};

const navItems = [
  { href: "/", label: "审计总控台", icon: LayoutDashboard },
  { href: "#", label: "智能体博弈", icon: Bot },
  { href: "#", label: "最终底稿中心", icon: FileText },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex h-full bg-slate-50">
        <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
          <div className="flex h-16 items-center gap-2 border-b border-slate-100 px-6">
            <span className="text-xl">⚡</span>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              AuditCore
            </span>
          </div>

          <nav className="flex flex-1 flex-col gap-1 p-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
                >
                  <Icon size={18} strokeWidth={1.75} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-slate-100 px-6 py-4">
            <p className="text-xs text-slate-400">AuditCore v1.0.0</p>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </body>
    </html>
  );
}