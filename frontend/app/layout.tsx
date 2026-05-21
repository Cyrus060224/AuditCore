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
  title: "AuditCore",
  description: "Enterprise-grade AI audit collaboration platform",
};

const navItems = [
  { href: "/", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Agent Arena", icon: Bot },
  { href: "/papers", label: "Working Papers", icon: FileText },
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
      <body className="flex h-full bg-white">
        {/* Sidebar */}
        <aside className="flex w-[200px] shrink-0 flex-col border-r border-gray-100">
          {/* Brand */}
          <div className="flex h-[56px] items-center px-5">
            <span className="text-sm font-semibold tracking-tight">AuditCore</span>
          </div>

          {/* Nav */}
          <nav className="flex flex-1 flex-col gap-0.5 px-3 py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.href === "/";
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors ${
                    isActive
                      ? "bg-gray-100 font-medium text-black"
                      : "text-gray-400 hover:bg-gray-50 hover:text-gray-700"
                  }`}
                >
                  <Icon size={15} strokeWidth={1.75} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

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
