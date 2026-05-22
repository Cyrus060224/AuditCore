"use client";

import React, { useEffect } from "react";
import { LanguageProvider, useTranslation } from "./i18n";
import SidebarNav from "./sidebar-nav";

function InnerLayout({ children }: { children: React.ReactNode }) {
  const { locale, setLocale, t } = useTranslation();

  // Dynamically update document lang attribute
  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

  return (
    <div className="flex h-full w-full bg-white">
      {/* Sidebar */}
      <aside className="flex w-[200px] shrink-0 flex-col border-r border-gray-100 bg-white">
        {/* Brand */}
        <div className="flex h-[56px] items-center px-5">
          <span className="text-sm font-semibold tracking-tight text-gray-900">
            {t("layout.title")}
          </span>
        </div>

        {/* Nav */}
        <SidebarNav />

        {/* Footer */}
        <div className="border-t border-gray-100 px-5 py-4">
          <p className="text-[11px] text-gray-300">
            {t("layout.version")}
          </p>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Topbar */}
        <header className="flex h-[56px] items-center justify-between border-b border-gray-100 px-8 bg-white">
          <p className="text-[13px] text-gray-400 font-medium">
            {t("layout.subtitle")}
          </p>
          
          {/* Beautiful modern HSL language switcher */}
          <div className="flex items-center gap-0.5 rounded-lg border border-gray-100 bg-gray-50/70 p-0.5 text-[11px] font-semibold">
            <button
              type="button"
              onClick={() => setLocale("zh")}
              className={`rounded-md px-2 py-0.5 transition-all duration-200 cursor-pointer ${
                locale === "zh"
                  ? "bg-white text-gray-900 shadow-xs ring-1 ring-black/5"
                  : "text-gray-400 hover:text-gray-700"
              }`}
            >
              中
            </button>
            <button
              type="button"
              onClick={() => setLocale("en")}
              className={`rounded-md px-2 py-0.5 transition-all duration-200 cursor-pointer ${
                locale === "en"
                  ? "bg-white text-gray-900 shadow-xs ring-1 ring-black/5"
                  : "text-gray-400 hover:text-gray-700"
              }`}
            >
              EN
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <div className="mx-auto max-w-[1120px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <InnerLayout>{children}</InnerLayout>
    </LanguageProvider>
  );
}
