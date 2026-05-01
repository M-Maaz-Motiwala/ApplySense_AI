import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>ApplySense AI Dashboard</h1>
      <p>Agent-assisted job application workflows with human approval gates.</p>
      <div className="row" style={{ marginTop: "1rem" }}>
        <Link href="/jobs">Jobs</Link>
        <Link href="/applications">Applications</Link>
      </div>
    </main>
  );
}
