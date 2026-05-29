"use client";

import { Bot, FileText, LayoutDashboard, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "./i18n";

const navItems = [
  { href: "/", translationKey: "nav.console", icon: LayoutDashboard },
  { href: "/arena", translationKey: "nav.arena", icon: Bot },
  { href: "/papers", translationKey: "nav.papers", icon: FileText },
  { href: "/settings", translationKey: "nav.settings", icon: Settings },
];

export default function SidebarNav() {
  const pathname = usePathname();
  const { t } = useTranslation();

  return (
    <nav className="flex flex-1 flex-col gap-0.5 px-3 py-2">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors ${
              isActive
                ? "bg-gray-100 font-medium text-black"
                : "text-gray-400 hover:bg-gray-50 hover:text-gray-700"
            }`}
          >
            <Icon size={15} strokeWidth={1.75} />
            {t(item.translationKey)}
          </Link>
        );
      })}
    </nav>
  );
}

