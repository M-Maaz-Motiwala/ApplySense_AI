import { getJobs } from "../../lib/api";
import { getToken } from "../../lib/auth";
import JobCard from "./JobCard";
import { SkeletonCard } from "../../components/ui/Loader";
import { Suspense } from "react";
import Link from "next/link";

async function JobList({ recommended }: { recommended: boolean }) {
  const jobs = await getJobs(recommended);
  const token = await getToken();

  return (
    <>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 border-b border-slate-200 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Available Roles</h1>
          <p className="text-slate-500 text-sm mt-1">
            {recommended ? "Showing jobs tailored to your profile." : "Browse all available opportunities."}
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <Link 
            href={recommended ? "/jobs" : "/jobs?recommended=true"}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all shadow-sm border ${
              recommended 
                ? "bg-indigo-600 text-white border-indigo-500 hover:bg-indigo-700" 
                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
            }`}
          >
            {recommended ? "✨ Showing Relevant" : "🎯 Filter Relevant"}
          </Link>
          <span className="bg-slate-100 text-slate-600 font-bold py-1 px-3 rounded-full text-xs">
            {jobs.length} roles
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {jobs.length > 0 ? (
          jobs.map((job: any) => (
            <JobCard key={job.id} job={job} token={token} />
          ))
        ) : (
          <div className="col-span-full py-20 text-center glass-panel">
            <h3 className="text-xl font-bold text-slate-800">No matching jobs found</h3>
            <p className="text-slate-500 mt-2">Try refreshing or viewing the global list.</p>
            <Link href="/jobs" className="text-indigo-600 font-semibold mt-4 inline-block hover:underline">
              View All Jobs &rarr;
            </Link>
          </div>
        )}
      </div>
    </>
  );
}

export default async function JobsPage({ searchParams }: { searchParams: Promise<{ recommended?: string }> }) {
  const { recommended } = await searchParams;
  const isRecommended = recommended === "true";

  return (
    <main className="py-8">
      <Suspense key={recommended} fallback={<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-16"><SkeletonCard/><SkeletonCard/><SkeletonCard/><SkeletonCard/></div>}>
        <JobList recommended={isRecommended} />
      </Suspense>
    </main>
  );
}
