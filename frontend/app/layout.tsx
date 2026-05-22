import type { Metadata } from "next";
import ClientLayout from "./client-layout";
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
      <body className="h-full bg-white font-sans antialiased text-[#1d1d1f]">
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}

