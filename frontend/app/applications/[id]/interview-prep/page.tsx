"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

const CLIENT_API = "http://localhost:8000/api/v1";

function getClientToken(): string {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? match[1] : "";
  }
  return "";
}

interface Question {
  question: string;
  tip: string;
}

export default function InterviewPrepPage() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);

  useEffect(() => {
    async function loadPrep() {
      try {
        const token = getClientToken();
        const res = await fetch(`${CLIENT_API}/applications/${id}/interview-prep`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (!res.ok) {
          throw new Error("Failed to load interview prep.");
        }

        const data = await res.json();
        setQuestions(data.questions || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      loadPrep();
    }
  }, [id]);

  return (
    <main className="py-12 max-w-4xl mx-auto px-4">
      <div className="mb-8 border-b border-slate-200 pb-4">
        <button 
          onClick={() => router.back()} 
          className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm mb-4 inline-flex items-center gap-1"
        >
          &larr; Back to Application
        </button>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          <span className="text-4xl">🎯</span> Interview Preparation
        </h1>
        <p className="text-slate-500 mt-2">
          Review these tailored questions and tips generated based on the job description.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-20">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Generating your personalized interview questions...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 text-red-700 p-6 rounded-xl border border-red-100 text-center">
          <p className="font-bold mb-2">Oops!</p>
          <p>{error}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {questions.map((q, idx) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-all">
              <h3 className="text-lg font-bold text-slate-900 mb-3 flex items-start gap-3">
                <span className="bg-indigo-100 text-indigo-700 w-6 h-6 rounded-full flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                {q.question}
              </h3>
              <div className="ml-9 bg-amber-50 border border-amber-100 rounded-lg p-4 text-sm text-slate-700">
                <strong className="text-amber-800 uppercase tracking-wider text-xs mb-1 block">💡 Pro Tip</strong>
                {q.tip}
              </div>
            </div>
          ))}

          <div className="mt-8 text-center bg-slate-50 border border-slate-200 rounded-xl p-8">
            <h3 className="font-bold text-slate-800 mb-2">You're ready!</h3>
            <p className="text-slate-500 mb-6 text-sm">Review these questions carefully and practice your answers using the STAR method.</p>
            <button 
              onClick={() => window.print()} 
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-6 rounded-lg shadow-sm transition-colors"
            >
              Print Cheat Sheet
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
