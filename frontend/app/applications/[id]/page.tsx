import { API_BASE } from "../../../lib/api";
import { getToken } from "../../../lib/auth";
import ApplicationActions from "./ApplicationActions";
import Link from "next/link";
import { Suspense } from "react";
import { SkeletonCard, SkeletonLine } from "../../../components/ui/Loader";

async function getApplicationPreview(id: string, token: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/preview-resume`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!res.ok) return null;
  return res.json();
}

async function ApplicationDetails({ id }: { id: string }) {
  const token = await getToken();
  const app = await getApplicationPreview(id, token);

  if (!app) {
    return (
      <div className="text-center py-16 glass-panel">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Application Not Found</h1>
        <p className="text-slate-500 mb-6">Could not load details or you are not authorized.</p>
        <Link href="/applications" className="bg-indigo-600 text-white py-2 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="flex justify-between items-center mb-8 border-b border-slate-200 pb-4">
        <div>
          <Link href="/applications" className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm mb-2 inline-flex items-center gap-1">
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Application Review</h1>
        </div>
        <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-4 py-2 rounded-lg font-bold shadow-sm">
          Match Score: <span className="text-indigo-900 text-xl">{app.match_score}%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Communications */}
        <div className="space-y-6">
          <section>
            <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-xl">✉️</span> Recruiter Email Draft
            </h2>
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm whitespace-pre-wrap text-sm text-slate-600 leading-relaxed font-mono">
              {app.email_draft}
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-xl">📝</span> Cover Letter
            </h2>
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm whitespace-pre-wrap text-sm text-slate-600 leading-relaxed font-serif">
              {app.cover_letter_text}
            </div>
          </section>

          <ApplicationActions applicationId={app.application_id} initialStatus={app.status} token={token} />
        </div>

        {/* Right Column: Resume Source */}
        <div className="space-y-6">
          <section className="h-full flex flex-col">
            <h2 className="text-lg font-bold text-slate-800 mb-1 flex items-center gap-2">
              <span className="text-xl">📄</span> Generated Resume
            </h2>
            <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider font-semibold">LaTeX Source Code</p>
            
            <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-inner overflow-hidden">
              <pre className="text-xs text-slate-300 font-mono overflow-y-auto h-full max-h-[700px] custom-scrollbar">
                {app.resume_latex_source}
              </pre>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}

export default async function ApplicationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <main className="py-8">
      <Suspense fallback={
        <div className="animate-pulse">
          <div className="mb-8"><SkeletonLine className="h-10 w-1/3" /></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div><SkeletonCard /><SkeletonCard /></div>
            <div className="h-[600px] bg-slate-200 rounded-xl"></div>
          </div>
        </div>
      }>
        <ApplicationDetails id={id} />
      </Suspense>
    </main>
  );
}
