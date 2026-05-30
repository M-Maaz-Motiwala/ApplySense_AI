import Link from "next/link";
import { getToken } from "../lib/auth";

export default async function HomePage() {
  const token = await getToken();

  return (
    <main className="flex flex-col items-center justify-center min-h-[calc(100vh-120px)] py-12 px-4 text-center">
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-50 to-transparent -z-10" />
      
      <div className="max-w-3xl mx-auto space-y-8 animate-in">
        <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Supercharge Your <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
            Job Applications
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          ApplySense AI automates the tedious parts of job hunting. We generate highly tailored cover letters, recruiter emails, and LaTeX resumes perfectly matched to real job descriptions.
        </p>

        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <Link 
            href="/jobs" 
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
          >
            Browse Jobs
          </Link>
          
          {!token ? (
            <Link 
              href="/auth/register" 
              className="bg-white hover:bg-slate-50 text-slate-900 border border-slate-200 font-bold py-3 px-8 rounded-lg shadow-sm hover:shadow-md transition-all"
            >
              Create Free Account
            </Link>
          ) : (
            <Link 
              href="/dashboard" 
              className="bg-white hover:bg-slate-50 text-indigo-600 border border-indigo-200 font-bold py-3 px-8 rounded-lg shadow-sm hover:shadow-md transition-all"
            >
              View Dashboard
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-5xl mx-auto">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-left hover:shadow-md transition-shadow">
          <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center text-2xl mb-6">🤖</div>
          <h3 className="text-xl font-bold text-slate-900 mb-3">AI Matching</h3>
          <p className="text-slate-600 leading-relaxed">Our LangGraph agent analyzes your profile against job requirements to calculate accurate match scores.</p>
        </div>
        
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-left hover:shadow-md transition-shadow">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center text-2xl mb-6">📄</div>
          <h3 className="text-xl font-bold text-slate-900 mb-3">Dynamic Resumes</h3>
          <p className="text-slate-600 leading-relaxed">Generates beautiful LaTeX resumes that highlight the exact skills the employer is looking for.</p>
        </div>
        
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-left hover:shadow-md transition-shadow">
          <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-2xl mb-6">✅</div>
          <h3 className="text-xl font-bold text-slate-900 mb-3">Human-in-the-Loop</h3>
          <p className="text-slate-600 leading-relaxed">Nothing gets sent without your approval. Review, edit, and approve all AI-generated assets.</p>
        </div>
      </div>
    </main>
  );
}
