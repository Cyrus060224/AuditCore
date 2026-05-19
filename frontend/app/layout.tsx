import type { Metadata } from "next";
import { Sidebar } from "./components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "AuditCore",
  description: "Industrial-grade multi-agent audit control plane",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full bg-slate-50 text-slate-900">
        <div className="flex min-h-screen">
          <Sidebar />
          {children}
        </div>
      </body>
    </html>
  );
}
