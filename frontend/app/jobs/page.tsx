import { getJobs } from "../../lib/api";
import { getToken } from "../../lib/auth";
import JobCard from "./JobCard";
import { SkeletonCard } from "../../../components/ui/Loader";
import { Suspense } from "react";

async function JobList() {
  const jobs = await getJobs();
  const token = await getToken();

  return (
    <>
      <div className="flex justify-between items-center mb-8 border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Available Roles</h1>
        <span className="bg-indigo-100 text-indigo-700 font-bold py-1 px-3 rounded-full text-sm">
          {jobs.length} jobs found
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {jobs.map((job: any) => (
          <JobCard key={job.id} job={job} token={token} />
        ))}
      </div>
    </>
  );
}

export default function JobsPage() {
  return (
    <main className="py-8">
      <Suspense fallback={<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-16"><SkeletonCard/><SkeletonCard/><SkeletonCard/><SkeletonCard/></div>}>
        <JobList />
      </Suspense>
    </main>
  );
}
