"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../../../components/ui/Button";

const CLIENT_API = "http://localhost:8000/api/v1";

export default function ApplicationActions({ applicationId, initialStatus, token }: { applicationId: string; initialStatus: string; token: string }) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [loadingAction, setLoadingAction] = useState<"approve" | "reject" | "discard" | null>(null);

  async function handleAction(action: "approve" | "reject" | "discard") {
    setLoadingAction(action);
    try {
      if (action === "approve") {
        const res = await fetch(`${CLIENT_API}/applications/${applicationId}/approve`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) setStatus("APPROVED");
      } else if (action === "reject") {
        const res = await fetch(`${CLIENT_API}/applications/${applicationId}/reject`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) setStatus("REJECTED");
      } else if (action === "discard") {
        await fetch(`${CLIENT_API}/applications/${applicationId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        router.push("/applications");
        return;
      }
      router.refresh();
    } catch (e) {
      console.error(e);
      alert(`Failed to ${action} application`);
    }
    setLoadingAction(null);
  }

  if (status !== "PENDING_APPROVAL") {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-center mt-6 shadow-sm">
        <div className="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-3 bg-white shadow-sm border border-slate-100 text-2xl">
          {status === "APPROVED" ? "✅" : "❌"}
        </div>
        <h3 className="font-bold text-slate-900 mb-1">Review Complete</h3>
        <p className="text-slate-500 text-sm">
          This application was <span className="font-bold text-slate-700">{status}</span>.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-indigo-100 shadow-sm rounded-xl p-6 mt-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-indigo-500" />
      
      <h3 className="text-lg font-bold text-slate-900 mb-2">Review Required</h3>
      <p className="text-slate-500 text-sm mb-6">
        Review the generated cover letter and email draft. If approved, the assets will be marked as ready to send.
      </p>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Button 
          variant="primary" 
          onClick={() => handleAction("approve")} 
          loading={loadingAction === "approve"}
          disabled={loadingAction !== null}
        >
          Approve & Keep
        </Button>
        <Button 
          variant="secondary" 
          onClick={() => handleAction("reject")} 
          loading={loadingAction === "reject"}
          disabled={loadingAction !== null}
        >
          Reject
        </Button>
        <Button 
          variant="danger" 
          onClick={() => handleAction("discard")} 
          loading={loadingAction === "discard"}
          disabled={loadingAction !== null}
        >
          Discard
        </Button>
      </div>
    </div>
  );
}
