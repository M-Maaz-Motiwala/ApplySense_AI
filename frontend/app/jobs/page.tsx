import { getJobs } from "../../lib/api";

export default async function JobsPage() {
  const jobs = await getJobs();

  return (
    <main>
      <h1>Jobs</h1>
      {jobs.map((job: any) => (
        <article key={job.id} className="card">
          <div className="row">
            <h2>{job.title}</h2>
            <span>{job.company}</span>
          </div>
          <p>{job.location}</p>
          <p>{job.raw_text_jd.slice(0, 220)}...</p>
        </article>
      ))}
    </main>
  );
}
