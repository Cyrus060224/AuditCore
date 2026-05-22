import type { Metadata } from "next";
import SidebarNav from "./sidebar-nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "AuditCore",
  description: "Enterprise-grade AI audit collaboration platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="flex h-full bg-white">
        {/* Sidebar */}
        <aside className="flex w-[200px] shrink-0 flex-col border-r border-gray-100">
          {/* Brand */}
          <div className="flex h-[56px] items-center px-5">
            <span className="text-sm font-semibold tracking-tight">AuditCore</span>
          </div>

          {/* Nav */}
          <SidebarNav />

          {/* Footer */}
          <div className="border-t border-gray-100 px-5 py-4">
            <p className="text-[11px] text-gray-300">v1.0.0</p>
          </div>
        </aside>

        {/* Main */}
        <div className="flex flex-1 flex-col">
          {/* Topbar */}
          <header className="flex h-[56px] items-center border-b border-gray-100 px-8">
            <p className="text-[13px] text-gray-400">
              Enterprise Penetration Audit System
            </p>
          </header>

          {/* Content */}
          <main className="flex-1 overflow-y-auto px-8 py-8">
            <div className="mx-auto max-w-[1120px]">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
