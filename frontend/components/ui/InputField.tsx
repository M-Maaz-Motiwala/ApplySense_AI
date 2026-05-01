"use client";

import { InputHTMLAttributes, forwardRef } from "react";

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  ({ label, error, className = "", ...props }, ref) => {
    return (
      <div className="w-full mb-4">
        <label className="block text-sm font-semibold text-slate-700 mb-1.5 uppercase tracking-wide">
          {label}
        </label>
        <input
          ref={ref}
          className={`w-full bg-white border ${
            error ? "border-red-400 focus:ring-red-100" : "border-slate-200 focus:ring-indigo-100 focus:border-indigo-500"
          } text-slate-900 px-3.5 py-2.5 rounded-lg shadow-sm transition-all outline-none focus:ring-4 ${className}`}
          {...props}
        />
        {error && <p className="mt-1.5 text-sm text-red-500 font-medium">{error}</p>}
      </div>
    );
  }
);
InputField.displayName = "InputField";
