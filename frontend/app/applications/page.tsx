import { getApplications } from "../../lib/api";
import Link from "next/link";
import { SkeletonLine } from "../../../components/ui/Loader";
import { Suspense } from "react";

function getStatusBadge(status: string) {
  switch (status) {
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

async function ApplicationList() {
  const apps = await getApplications();

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
      {apps.map((app: any) => (
        <div key={app.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-all flex items-center justify-between group">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-bold text-lg text-slate-900">{app.job?.title || "Application"}</h2>
              {getStatusBadge(app.status)}
            </div>
            <p className="text-sm text-slate-500">
              {app.job?.company} • Generated on {new Date(app.created_at).toLocaleDateString()}
            </p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Match Score</span>
              <span className={`text-lg font-bold ${app.match_score >= 80 ? 'text-emerald-600' : 'text-slate-700'}`}>
                {app.match_score}%
              </span>
            </div>
            
            <Link 
              href={`/applications/${app.id}`} 
              className="bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-indigo-600 font-semibold py-2 px-4 rounded-lg transition-all"
            >
              Review Details &rarr;
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ApplicationsPage() {
  return (
    <main className="py-8">
      <div className="mb-8 border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Your Applications</h1>
        <p className="text-slate-500 mt-2">Manage and review your AI-generated cover letters and resumes.</p>
      </div>

      <Suspense fallback={
        <div className="space-y-4">
          {[1,2,3].map(i => (
            <div key={i} className="bg-white border border-slate-200 rounded-xl p-6 h-28 flex items-center animate-pulse">
              <div className="w-full">
                <SkeletonLine className="h-5 w-1/4 mb-2" />
                <SkeletonLine className="h-4 w-1/3" />
              </div>
            </div>
          ))}
        </div>
      }>
        <ApplicationList />
      </Suspense>
    </main>
  );
}
