"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { zh } from "./zh";
import { en } from "./en";

export type Locale = "zh" | "en";

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, replacements?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const dictionaries = { zh, en };

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("zh");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Read from localStorage on mount
    const saved = localStorage.getItem("auditcore.locale") as Locale;
    if (saved === "zh" || saved === "en") {
      setLocaleState(saved);
    } else {
      // Try system language preference
      const sysLang = navigator.language.toLowerCase();
      if (sysLang.startsWith("en")) {
        setLocaleState("en");
      } else {
        setLocaleState("zh");
      }
    }
    setMounted(true);
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem("auditcore.locale", newLocale);
  };

  const t = (key: string, replacements?: Record<string, string | number>): string => {
    const dict = dictionaries[locale] || dictionaries.zh;
    
    // Resolve nested keys e.g., 'nav.console'
    const val = key.split(".").reduce((acc: any, part) => {
      return acc && acc[part];
    }, dict);

    if (typeof val !== "string") {
      // Fallback to zh if not found in current locale
      const fallbackDict = dictionaries.zh;
      const fallbackVal = key.split(".").reduce((acc: any, part) => {
        return acc && acc[part];
      }, fallbackDict);

      if (typeof fallbackVal === "string") {
        return replacePlaceholders(fallbackVal, replacements);
      }
      return key;
    }

    return replacePlaceholders(val, replacements);
  };

  function replacePlaceholders(str: string, replacements?: Record<string, string | number>): string {
    if (!replacements) return str;
    return Object.entries(replacements).reduce((acc, [k, v]) => {
      return acc.replace(new RegExp(`{${k}}`, "g"), String(v));
    }, str);
  }

  // To prevent hydration mismatch in NextJS, we don't render children until mounted is true.
  // Actually, we can render children immediately, but having a state might lead to a slight flash.
  // However, Next.js 13+ app router layout wrapping client components requires good hydration practices.
  // Letting it render children directly ensures we don't block layout render.
  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useTranslation must be used within a LanguageProvider");
  }
  return context;
}
