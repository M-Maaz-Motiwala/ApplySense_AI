"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Application {
  id: string;
  status: string;
  match_score: number;
  last_updated: string;
  job?: {
    title: string;
    company: string;
  };
}

function getStatusBadge(app: Application) {
  const status = app.status;
  const progress = (app as any).advisor_feedback?.progress;
  const msg = (app as any).advisor_feedback?.status_message;

  switch (status) {
    case "GENERATING":
      return (
        <div className="flex flex-col items-end gap-1">
          <span className="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-200 animate-pulse flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" />
            AI: {msg || "Generating..."}
          </span>
          {progress && (
            <div className="w-24 bg-slate-100 h-1 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full transition-all duration-500" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>
      );
    case "PENDING_APPROVAL":
      return <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">Pending Review</span>;
    case "APPROVED":
      return <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full border border-emerald-200">Approved</span>;
    case "REJECTED":
      return <span className="bg-red-100 text-red-800 text-xs font-bold px-3 py-1 rounded-full border border-red-200">Rejected</span>;
    default:
      return <span className="bg-slate-100 text-slate-800 text-xs font-bold px-3 py-1 rounded-full border border-slate-200">{status}</span>;
  }
}

export default function RealTimeApplicationList({ 
  initialApps, 
  token 
}: { 
  initialApps: Application[]; 
  token: string;
}) {
  const [apps, setApps] = useState(initialApps);

  useEffect(() => {
    const hasProcessing = apps.some(app => app.status === "GENERATING");
    if (!hasProcessing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/applications", {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setApps(data);
          
          const stillProcessing = data.some((app: any) => app.status === "GENERATING");
          if (!stillProcessing) {
            clearInterval(interval);
          }
        }
      } catch (e) {
        console.error("Polling failed", e);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [apps, token]);

  if (apps.length === 0) {
    return (
      <div className="text-center py-16 bg-white border border-slate-200 rounded-xl shadow-sm">
        <h2 className="text-xl font-bold text-slate-700 mb-2">No Applications Yet</h2>
        <p className="text-slate-500 mb-6">Head over to the Jobs tab to generate your first application.</p>
        <Link href="/jobs" className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors">
          Browse Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      {apps.map((app) => (
        <div key={app.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-all flex items-center justify-between group">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-bold text-lg text-slate-900">{app.job?.title || "Application"}</h2>
              {getStatusBadge(app)}
            </div>
            <p className="text-sm text-slate-500" suppressHydrationWarning>
              {app.job?.company} • Updated {app.last_updated ? new Date(app.last_updated).toLocaleDateString() : "Just now"}
            </p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Match Score</span>
              <span className={`text-lg font-bold ${app.match_score >= 80 ? 'text-emerald-600' : 'text-slate-700'}`}>
                {app.match_score}%
              </span>
            </div>
            
            {app.status === "GENERATING" ? (
              <div className="bg-slate-100 text-slate-400 font-semibold py-2 px-4 rounded-lg cursor-not-allowed border border-slate-200">
                Processing...
              </div>
            ) : (
              <Link 
                href={`/applications/${app.id}`} 
                className="bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-indigo-600 font-semibold py-2 px-4 rounded-lg transition-all"
              >
                Review Details &rarr;
              </Link>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
