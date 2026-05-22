"use client";

import { Bot, FileText, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Agent Arena", icon: Bot },
  { href: "/papers", label: "Working Papers", icon: FileText },
];

export default function SidebarNav() {
  const pathname = usePathname();

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
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
