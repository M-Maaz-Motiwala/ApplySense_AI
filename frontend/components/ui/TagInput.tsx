"use client";

import { useState, KeyboardEvent } from "react";

interface TagInputProps {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  suggestions?: string[];
}

export function TagInput({ label, tags, onChange, placeholder = "Press Enter to add...", suggestions = [] }: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === "Backspace" && !inputValue && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  const addTag = (val: string) => {
    const newTag = val.trim();
    if (newTag && !tags.includes(newTag)) {
      onChange([...tags, newTag]);
    }
    setInputValue("");
  };

  const removeTag = (indexToRemove: number) => {
    onChange(tags.filter((_, i) => i !== indexToRemove));
  };

  // Filter out suggestions that are already added
  const availableSuggestions = suggestions.filter(s => !tags.includes(s));

  return (
    <div className="w-full mb-4">
      <label className="block text-sm font-semibold text-slate-700 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      
      {availableSuggestions.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {availableSuggestions.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => addTag(s)}
              className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-1 rounded-md text-xs font-bold hover:bg-emerald-100 transition-colors"
            >
              + {s}
            </button>
          ))}
        </div>
      )}

      <div className="w-full bg-white border border-slate-200 text-slate-900 p-2 rounded-lg shadow-sm focus-within:ring-4 focus-within:ring-indigo-100 focus-within:border-indigo-500 transition-all min-h-[46px] flex flex-wrap gap-2 items-center">
        {tags.map((tag, index) => (
          <span
            key={index}
            className="flex items-center gap-1.5 bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md text-sm font-medium border border-indigo-100"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="text-indigo-400 hover:text-indigo-900 focus:outline-none"
            >
              &times;
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={tags.length === 0 ? placeholder : ""}
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm placeholder:text-slate-400"
        />
      </div>
      <p className="mt-1 text-xs text-slate-400">Type and press Enter to add multiple items.</p>
    </div>
  );
}
