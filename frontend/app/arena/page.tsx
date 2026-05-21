"use client";

import { ArrowLeft, Bot } from "lucide-react";
import Link from "next/link";

export default function AgentArena() {
  return (
    <div>
      <div className="mb-12">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-700"
        >
          <ArrowLeft size={14} />
          Back
        </Link>
      </div>

      <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-50">
          <Bot size={24} className="text-gray-400" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight">
          Agent Arena
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          Multi-agent adversarial analysis
        </p>
        <div className="mt-8 rounded-full bg-gray-50 px-4 py-1.5">
          <span className="text-xs font-medium text-gray-400">
            Coming soon
          </span>
        </div>
      </div>
    </div>
  );
}
