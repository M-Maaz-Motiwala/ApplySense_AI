"use client";

import { useState } from "react";
import { approveApplication, rejectApplication } from "../../lib/api";

export function Actions({ applicationId }: { applicationId: string }) {
  const [status, setStatus] = useState<string>("");

  async function approve() {
    const res = await approveApplication(applicationId);
    setStatus(res.status);
  }

  async function reject() {
    const res = await rejectApplication(applicationId);
    setStatus(res.status);
  }

  return (
    <div className="row">
      <div>
        <button className="approve" onClick={approve}>
          Approve
        </button>
        <button className="reject" onClick={reject} style={{ marginLeft: "0.5rem" }}>
          Reject
        </button>
      </div>
      <span>{status}</span>
    </div>
  );
}
