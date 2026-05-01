"use client";

import { useState } from "react";
import { Button } from "./Button";
import { InputField } from "./InputField";

interface BulletEditorProps {
  label: string;
  bullets: string[];
  onChange: (bullets: string[]) => void;
  token?: string; // Needed for API calls
}

export function BulletEditor({ label, bullets, onChange, token }: BulletEditorProps) {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!description.trim()) {
      setError("Please write a description first.");
      return;
    }
    
    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/llm/generate-bullets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ description })
      });

      if (!res.ok) throw new Error("Failed to generate bullets");
      const data = await res.json();
      
      // Combine existing with new
      onChange([...bullets, ...data.bullets]);
      setDescription(""); // clear textarea
    } catch (err) {
      setError("Could not generate suggestions. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const updateBullet = (index: number, val: string) => {
    const newB = [...bullets];
    newB[index] = val;
    onChange(newB);
  };

  const removeBullet = (index: number) => {
    onChange(bullets.filter((_, i) => i !== index));
  };

  const addManualBullet = () => {
    onChange([...bullets, ""]);
  };

  return (
    <div className="w-full mb-6 bg-slate-50 border border-slate-200 rounded-lg p-4">
      <label className="block text-sm font-bold text-slate-900 mb-2">{label}</label>
      
      <div className="mb-4">
        <textarea
          className="w-full bg-white border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
          rows={3}
          placeholder="Describe your responsibilities and achievements in a paragraph..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-slate-500 italic">We will use AI to convert this into professional bullets.</p>
          <Button type="button" variant="primary" onClick={handleGenerate} loading={loading} className="py-1.5 px-3 text-xs">
            ✨ Generate AI Bullets
          </Button>
        </div>
        {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
      </div>

      {bullets.length > 0 && (
        <div className="space-y-2 mt-4">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">Final Bullets</label>
          {bullets.map((b, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="mt-2 text-slate-400">•</span>
              <textarea
                className="flex-1 bg-white border border-slate-200 rounded-md p-2 text-sm outline-none focus:border-indigo-500"
                value={b}
                onChange={(e) => updateBullet(i, e.target.value)}
                rows={2}
              />
              <button type="button" onClick={() => removeBullet(i)} className="mt-2 text-red-400 hover:text-red-600 font-bold">
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
      
      <button type="button" onClick={addManualBullet} className="mt-3 text-xs font-bold text-indigo-600 hover:text-indigo-800">
        + Add Bullet Manually
      </button>
    </div>
  );
}
