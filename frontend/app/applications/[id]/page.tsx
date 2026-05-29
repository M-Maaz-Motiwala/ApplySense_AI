import { API_BASE } from "../../../lib/api";
import { getToken } from "../../../lib/auth";
import ResumeViewer from "./ResumeViewer";
import ApplicationActions from "./ApplicationActions";
import CritiqueSection from "./CritiqueSection";
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
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Review for {app.job_title}
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            {app.company} • <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">View Original Job &nearr;</a>
          </p>
        </div>
        <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-4 py-2 rounded-lg font-bold shadow-sm">
          Match Score: <span className="text-indigo-900 text-xl">{app.match_score}%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Communications */}
        <div className="space-y-6 flex flex-col">
          {app.advisor_feedback && (
            <CritiqueSection 
              applicationId={app.application_id} 
              feedback={app.advisor_feedback} 
              token={token} 
            />
          )}

          <section>
            <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-xl">✉️</span> Recruiter Email Draft
            </h2>
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm whitespace-pre-wrap text-sm text-slate-600 leading-relaxed font-mono">
              {app.email_draft}
            </div>
          </section>

          <section className="flex-1 flex flex-col">
            <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <span className="text-xl">📝</span> Cover Letter
            </h2>
            <div className="flex-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm whitespace-pre-wrap text-sm text-slate-600 leading-relaxed font-serif">
              {app.cover_letter_text}
            </div>
          </section>

          <div className="mt-auto pt-6">
            <ApplicationActions applicationId={app.application_id} initialStatus={app.status} token={token} />
          </div>
        </div>

        {/* Right Column: Resume Viewer */}
        <div className="space-y-6">
          <ResumeViewer 
            applicationId={app.application_id} 
            latexSource={app.resume_latex_source} 
            token={token} 
          />
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
