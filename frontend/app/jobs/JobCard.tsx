"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../../components/ui/Button";

const CLIENT_API = "http://localhost:8000/api/v1";

function getClientToken(): string {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? match[1] : "";
  }
  return "";
}

export default function JobCard({ job, token }: { job: any; token?: string }) {
  const router = useRouter();
  const [matchScore, setMatchScore] = useState<number | null>(job.match_score ?? null);
  const [advisor, setAdvisor] = useState<any>(job.advisor ?? null);
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  function authToken() {
    return token || getClientToken();
  }

  async function calculateMatch() {
    setLoadingMatch(true);
    try {
      const res = await fetch(`${CLIENT_API}/jobs/${job.id}/match`, {
        headers: { Authorization: `Bearer ${authToken()}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMatchScore(data.score);
        setAdvisor(data.advisor);
      }
    } catch (e) {
      console.error(e);
    }
    setLoadingMatch(false);
  }

  async function generateApplication() {
    setGenerating(true);
    try {
      const res = await fetch(`${CLIENT_API}/jobs/${job.id}/generate-application`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken()}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTaskId(data.task_id);
        router.refresh();
        router.push("/applications");
      }
    } catch (e) {
      console.error(e);
      setGenerating(false);
    }
  }

  return (
    <article className="glass-panel p-6 hover:shadow-md transition-shadow relative overflow-hidden group">
      {/* Dynamic Match Score Background Highlight */}
      {matchScore !== null && (
        <div 
          className={`absolute top-0 left-0 w-1.5 h-full ${
            matchScore >= 80 ? "bg-emerald-500" : matchScore >= 50 ? "bg-amber-500" : "bg-red-500"
          }`} 
        />
      )}
      
      <div className="flex justify-between items-start mb-2">
        <div>
          <h2 className="text-xl font-bold text-slate-900 leading-tight">{job.title}</h2>
          {job.source_url && (
            <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 text-sm hover:underline flex items-center gap-1 mt-1">
              View Original Job ↗
            </a>
          )}
        </div>
        <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
          {job.source}
        </span>
      </div>
      
      <p className="text-indigo-600 font-semibold mb-3 text-sm">
        {job.company} <span className="text-slate-400 font-normal mx-1">•</span> {job.location}
      </p>

      {/* Career Advisor Quick Insights */}
      {advisor && (
        <div className="flex flex-wrap gap-2 mb-4">
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-tight ${
            advisor.confidence === 'High' ? 'bg-emerald-100 text-emerald-700' : 
            advisor.confidence === 'Moderate' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
          }`}>
            {advisor.confidence} Confidence
          </span>
          {advisor.missing_skills?.length > 0 && (
            <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full uppercase tracking-tight">
              Missing: {advisor.missing_skills.slice(0, 2).join(", ")}
            </span>
          )}
        </div>
      )}
      
      <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 mb-6 text-sm text-slate-600 h-[100px] overflow-hidden relative">
        {job.raw_text_jd.slice(0, 300)}...
        {/* Fade out text effect */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-50 to-transparent" />
      </div>

      {advisor && (
        <div className="mb-6 p-4 bg-indigo-50/50 rounded-lg border border-indigo-100 animate-in fade-in slide-in-from-top-2">
          <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2">Career Advisor Insights</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Strengths</p>
              <div className="flex flex-wrap gap-1">
                {advisor.strengths.slice(0, 3).map((s: string) => (
                  <span key={s} className="text-[9px] bg-emerald-100 text-emerald-800 px-1.5 rounded">✓ {s}</span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Readiness</p>
              <div className="flex items-center gap-1.5">
                <div className="flex-1 bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-indigo-600 h-full" style={{ width: `${advisor.readiness_score}%` }} />
                </div>
                <span className="text-[10px] font-bold text-indigo-700">{advisor.readiness_score}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {matchScore === null ? (
          <Button variant="secondary" onClick={calculateMatch} loading={loadingMatch} className="flex-1">
            Calculate Match Score
          </Button>
        ) : (
          <div className="flex items-center gap-2 bg-white border border-slate-200 px-4 py-2 rounded-lg font-bold flex-1 justify-center">
            <span className="text-xs text-slate-500 uppercase">Match:</span>
            <span className={`text-lg ${matchScore >= 80 ? 'text-emerald-600' : matchScore >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
              {matchScore}%
            </span>
          </div>
        )}

        <Button 
          variant="primary" 
          onClick={generateApplication} 
          loading={generating}
          disabled={taskId !== null}
          className="flex-1"
        >
          {taskId ? "Task Queued" : "Generate Application"}
        </Button>
      </div>
    </article>
  );
}
