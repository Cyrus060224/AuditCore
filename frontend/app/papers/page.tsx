"use client";

import { ArrowLeft, FileText } from "lucide-react";
import Link from "next/link";

export default function WorkingPapers() {
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
          <FileText size={24} className="text-gray-400" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight">
          Working Papers
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          Centralized audit documentation
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
