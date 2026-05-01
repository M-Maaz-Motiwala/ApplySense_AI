"use client";

import { useState, useEffect } from "react";

interface DateRangePickerProps {
  label: string;
  value: string;
  onChange: (val: string) => void;
  single?: boolean;
}

// Helper to format YYYY-MM to "MMM YYYY"
function formatMonthYear(yyyymm: string) {
  if (!yyyymm) return "";
  const [year, month] = yyyymm.split("-");
  const date = new Date(parseInt(year), parseInt(month) - 1);
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export function DateRangePicker({ label, value, onChange, single = false }: DateRangePickerProps) {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  // Attempt to parse existing "MMM YYYY -- MMM YYYY" on mount
  useEffect(() => {
    if (value && value.includes(" -- ")) {
      // Basic reverse parsing isn't perfect for all formats, 
      // but we will mainly rely on this component generating the string.
      // For simplicity, we just sync the outgoing string when inputs change.
    }
  }, [value]);

  const handleStart = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStart = e.target.value;
    setStart(newStart);
    emitChange(newStart, end);
  };

  const handleEnd = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnd = e.target.value;
    setEnd(newEnd);
    emitChange(start, newEnd);
  };

  const emitChange = (s: string, e: string) => {
    if (!s) {
      onChange("");
      return;
    }
    const startStr = formatMonthYear(s);
    if (single) {
      onChange(startStr);
      return;
    }
    const endStr = e ? formatMonthYear(e) : "Present";
    onChange(`${startStr} -- ${endStr}`);
  };

  // Get today's YYYY-MM for max attribute
  const today = new Date();
  const maxMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;

  return (
    <div className="w-full">
      <label className="block text-sm font-semibold text-slate-700 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <input
            type="month"
            max={maxMonth}
            value={start}
            onChange={handleStart}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 transition-all text-slate-900"
          />
          <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide">{single ? "Date" : "Start Date"}</p>
        </div>
        {!single && (
          <>
            <span className="text-slate-400 text-sm font-bold">--</span>
            <div className="flex-1">
              <input
                type="month"
                max={maxMonth}
                value={end}
                onChange={handleEnd}
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 transition-all text-slate-900"
              />
              <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide">End Date (Leave blank for Present)</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
