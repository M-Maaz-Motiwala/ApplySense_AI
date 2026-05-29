import { getApplications } from "../../lib/api";
import { SkeletonLine } from "../../components/ui/Loader";
import { Suspense } from "react";
import { redirect } from "next/navigation";
import { getToken } from "../../lib/auth";
import RealTimeApplicationList from "../../components/applications/RealTimeApplicationList";

async function ApplicationListWrapper() {
  const token = await getToken();
  let apps;
  try {
    apps = await getApplications();
  } catch (err: any) {
    if (err.message === "Unauthorized") {
      redirect("/auth/login");
    }
    throw err;
  }

  return <RealTimeApplicationList initialApps={apps} token={token} />;
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
        <ApplicationListWrapper />
      </Suspense>
    </main>
  );
}
