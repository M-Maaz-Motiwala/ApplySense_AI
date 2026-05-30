"use client";

import { useState, useEffect } from "react";
import { Button } from "./Button";
import { Progress } from "./Progress";
import { CLIENT_API_BASE } from "../../lib/api";

export function RefreshJobsButton({ token }: { token: string }) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleRefresh = async () => {
    setLoading(true);
    setProgress(10);
    setStatusMsg("Starting job search...");
    try {
      const res = await fetch(`${CLIENT_API_BASE}/jobs/refresh`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTaskId(data.task_id);
      } else {
        setStatusMsg("Failed to start job search.");
        setLoading(false);
      }
    } catch (e) {
      setStatusMsg("Connection error.");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    let pollCount = 0;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${CLIENT_API_BASE}/tasks/${taskId}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data.result?.progress) setProgress(data.result.progress);
          if (data.result?.status_message) setStatusMsg(data.result.status_message);

          if (data.status === "COMPLETED") {
            setLoading(false);
            setTaskId(null);
            clearInterval(interval);
            setTimeout(() => { setStatusMsg(""); setProgress(0); }, 5000);
          } else if (data.status === "FAILED") {
            setStatusMsg("Job search failed.");
            setLoading(false);
            setTaskId(null);
            clearInterval(interval);
          }
        }
      } catch (e) {
        console.error("Polling error", e);
      }
      
      pollCount++;
      if (pollCount > 100) { // Safety timeout
        clearInterval(interval);
        setLoading(false);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, token]);

  return (
    <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔍</span>
          <div>
            <h3 className="font-bold text-slate-900">Find New Jobs</h3>
            <p className="text-xs text-slate-500">Scan 20+ sources for new roles.</p>
          </div>
        </div>
        {!loading && (
          <Button 
            variant="secondary" 
            onClick={handleRefresh} 
            size="sm"
            className="shadow-sm"
          >
            Start Scan
          </Button>
        )}
      </div>

      {loading && (
        <div className="space-y-2 animate-in fade-in duration-300">
          <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
            <span>{statusMsg}</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} className="h-1.5" />
        </div>
      )}
      
      {!loading && statusMsg && (
        <p className="text-xs font-bold text-emerald-600 flex items-center gap-1">
          <span className="text-sm">✅</span> {statusMsg}
        </p>
      )}
    </div>
  );
}
