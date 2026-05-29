"use client";

import { useState } from "react";
import { CLIENT_API_BASE } from "../../../lib/api";
import { Button } from "../../../components/ui/Button";

interface CritiqueItem {
  text: string;
  type: string;
  skill?: string;
}

interface AdvisorFeedback {
  quality_score: number;
  critique: CritiqueItem[];
  attempts: number;
}

export default function CritiqueSection({ 
  applicationId, 
  feedback, 
  token 
}: { 
  applicationId: string; 
  feedback: AdvisorFeedback; 
  token: string;
}) {
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedCritique, setSelectedCritique] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev => 
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    );
  };

  const toggleCritique = (text: string) => {
    setSelectedCritique(prev => 
      prev.includes(text) ? prev.filter(t => t !== text) : [...prev, text]
    );
  };

  const handleRegenerate = async () => {
    if (selectedSkills.length === 0 && selectedCritique.length === 0) {
      setMsg("Please select at least one item to address.");
      return;
    }
    setLoading(true);
    setMsg("");
    try {
      const res = await fetch(`${CLIENT_API_BASE}/applications/${applicationId}/regenerate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ 
          approved_skills: selectedSkills,
          approved_critique: selectedCritique
        })
      });
      
      if (res.ok) {
        setMsg("Regeneration started! Redirecting to applications list...");
        setTimeout(() => window.location.href = "/applications", 3000);
      } else {
        setMsg("Failed to start regeneration.");
      }
    } catch (e) {
      setMsg("Connection error.");
    } finally {
      setLoading(false);
    }
  };

  const rawCritique = feedback.critique || [];
  
  // Robustly handle different feedback formats (objects or strings)
  const normalizedCritique = rawCritique.map(item => {
    if (typeof item === 'string') {
      const lower = item.toLowerCase();
      if (lower.includes("suggest") || lower.includes("missing") || lower.includes("add")) {
        const words = item.split(" ");
        const skill = words.find(w => w.length > 2 && !["missing", "suggest", "adding", "skill"].includes(w.toLowerCase()));
        return { text: item, type: "skill_suggestion", skill: skill || "New Skill" };
      }
      return { text: item, type: "improvement" };
    }
    return item;
  });

  return (
    <section className="bg-indigo-900 text-white rounded-xl p-5 shadow-lg border border-indigo-700 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <span className="text-xl">🤖</span> AI Agent Critique
        </h2>
        <div className="bg-white/20 px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md border border-white/10">
          Quality Score: {feedback.quality_score}/100
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="bg-white/10 rounded-lg p-3 border border-white/5">
          <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-300 mb-2">Check items to address in next version:</h3>
          <div className="space-y-3">
            {normalizedCritique.map((item, i) => (
              <label key={i} className="flex items-start gap-3 cursor-pointer group">
                <input 
                  type="checkbox" 
                  className="mt-1 w-4 h-4 rounded border-white/20 bg-white/10 text-indigo-500 focus:ring-offset-indigo-900" 
                  checked={item.skill ? selectedSkills.includes(item.skill) : selectedCritique.includes(item.text)}
                  onChange={() => {
                    if (item.skill) toggleSkill(item.skill);
                    else toggleCritique(item.text);
                  }}
                />
                <div className="flex flex-col">
                  <span className={`text-sm ${item.skill ? 'text-indigo-100 italic' : 'text-slate-100'} group-hover:text-white transition-colors`}>
                    {item.text}
                  </span>
                  {item.type === 'skill_suggestion' && (
                    <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-tighter mt-0.5">Missing Skill Detected</span>
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-white/10 flex flex-col gap-3">
          <Button 
            onClick={handleRegenerate} 
            loading={loading}
            className="w-full bg-white text-indigo-900 hover:bg-indigo-50 border-none font-bold shadow-md py-2"
          >
            🔄 Regenerate Selected Improvements
          </Button>
          
          {msg && <p className="text-xs font-bold text-emerald-400 animate-pulse text-center">{msg}</p>}

          <div className="flex items-center justify-between">
            <p className="text-[10px] text-indigo-300 font-medium uppercase tracking-widest">
              Agent Loop: {feedback.attempts} Attempts
            </p>
            <div className="flex gap-1">
              {[...Array(feedback.attempts)].map((_, i) => (
                <div key={i} className="w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
