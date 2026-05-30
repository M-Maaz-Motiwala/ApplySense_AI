"use client";
import { useState } from "react";
import { API_BASE } from "../../../lib/api";

interface ResumeViewerProps {
  applicationId: string;
  latexSource: string;
  token: string;
}

export default function ResumeViewer({ applicationId, latexSource, token }: ResumeViewerProps) {
  const [activeTab, setActiveTab] = useState<"source" | "preview">("preview");

  const pdfUrl = `${API_BASE}/applications/${applicationId}/resume.pdf?token=${token}`;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
          <span className="text-xl">📄</span> Generated Resume
        </h2>
        
        <div className="flex bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab("preview")}
            className={`px-3 py-1 text-xs font-bold rounded-md transition ${
              activeTab === "preview" 
                ? "bg-white text-indigo-600 shadow-sm" 
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            PREVIEW (PDF)
          </button>
          <button
            onClick={() => setActiveTab("source")}
            className={`px-3 py-1 text-xs font-bold rounded-md transition ${
              activeTab === "source" 
                ? "bg-white text-indigo-600 shadow-sm" 
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            SOURCE (LATEX)
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden min-h-[600px] flex flex-col">
        {activeTab === "source" ? (
          <div className="bg-slate-900 p-5 h-full overflow-hidden">
             <pre className="text-xs text-slate-300 font-mono overflow-y-auto h-full max-h-[700px] custom-scrollbar">
                {latexSource}
              </pre>
          </div>
        ) : (
          <iframe 
            src={pdfUrl} 
            className="w-full h-full border-none"
            title="Resume Preview"
          />
        )}
      </div>
      
      <div className="mt-3 flex justify-end">
        <a 
          href={pdfUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
        >
          <span>📥</span> Download PDF
        </a>
      </div>
    </div>
  );
}
