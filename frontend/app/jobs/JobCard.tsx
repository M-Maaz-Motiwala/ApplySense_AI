"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../../../components/ui/Button";

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
  const [matchScore, setMatchScore] = useState<number | null>(null);
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
        alert("Application generation started! Check the Applications tab in a few minutes.");
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
        <h2 className="text-xl font-bold text-slate-900 leading-tight">{job.title}</h2>
        <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">
          {job.source}
        </span>
      </div>
      
      <p className="text-indigo-600 font-semibold mb-4 text-sm">
        {job.company} <span className="text-slate-400 font-normal mx-1">•</span> {job.location}
      </p>
      
      <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 mb-6 text-sm text-slate-600 h-[120px] overflow-hidden relative">
        {job.raw_text_jd.slice(0, 300)}...
        {/* Fade out text effect */}
        <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-slate-50 to-transparent" />
      </div>

      <div className="flex flex-wrap items-center gap-4">
        {matchScore === null ? (
          <Button variant="secondary" onClick={calculateMatch} loading={loadingMatch}>
            Calculate Match Score
          </Button>
        ) : (
          <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 px-4 py-2 rounded-lg font-bold">
            <span>Match Score:</span>
            <span className="text-lg">{matchScore}%</span>
          </div>
        )}

        <Button 
          variant="primary" 
          onClick={generateApplication} 
          loading={generating}
          disabled={taskId !== null}
        >
          {taskId ? "Task Queued" : "Generate Application"}
        </Button>
      </div>
    </article>
  );
}
