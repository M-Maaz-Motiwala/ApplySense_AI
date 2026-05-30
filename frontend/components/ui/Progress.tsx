"use client";

import * as React from "react";

export function Progress({ value = 0, className = "" }: { value?: number, className?: string }) {
  return (
    <div className={`relative h-2 w-full overflow-hidden rounded-full bg-slate-100 ${className}`}>
      <div
        className="h-full w-full flex-1 bg-indigo-600 transition-all duration-500 ease-in-out"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </div>
  );
}
