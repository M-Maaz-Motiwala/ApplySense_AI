"use client";

import { useState } from "react";
import { Button } from "./Button";

export function RefreshJobsButton({ token }: { token: string }) {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleRefresh = async () => {
    setLoading(true);
    setMsg("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/jobs/refresh", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        setMsg("Job search triggered! Check back in a few minutes.");
      } else {
        setMsg("Failed to start job search.");
      }
    } catch (e) {
      setMsg("Connection error.");
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(""), 5000);
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <Button 
        variant="secondary" 
        onClick={handleRefresh} 
        loading={loading}
        className="w-full"
      >
        🔍 Find New Jobs Now
      </Button>
      {msg && <p className="text-xs font-bold text-indigo-600 animate-pulse">{msg}</p>}
    </div>
  );
}
