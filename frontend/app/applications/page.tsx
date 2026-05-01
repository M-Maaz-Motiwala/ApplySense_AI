import { getApplications } from "../../lib/api";
import { Actions } from "./Actions";

export default async function ApplicationsPage() {
  const applications = await getApplications();

  return (
    <main>
      <h1>Applications</h1>
      {applications.map((app: any) => (
        <article key={app.id} className="card">
          <div className="row">
            <h2>{app.status}</h2>
            <span>Match Score: {app.match_score}</span>
          </div>
          <p>Job ID: {app.job_id}</p>
          <Actions applicationId={app.id} />
        </article>
      ))}
    </main>
  );
}
