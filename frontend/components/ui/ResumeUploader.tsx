"use client";

import { useState } from "react";
import { Button } from "./Button";
import { Spinner } from "./Loader";

interface ResumeUploaderProps {
  onSuccess: (data: any) => void;
  token?: string;
}

export function ResumeUploader({ onSuccess, token }: ResumeUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${baseUrl}/resumes/parse`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) throw new Error("Failed to parse resume");
      
      const data = await res.json();
      onSuccess(data); // Returns the parsed schema
    } catch (err) {
      setError("Failed to parse resume. You can skip this step and fill manually.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full border-2 border-dashed border-indigo-200 rounded-xl p-8 text-center bg-indigo-50/30 hover:bg-indigo-50/50 transition-colors">
      <div className="text-4xl mb-4">📄</div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">Upload Existing Resume (Optional)</h3>
      <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
        We will use AI to extract your experience, education, and skills to autofill the rest of the profile builder.
      </p>

      <input 
        type="file" 
        accept=".pdf,.doc,.docx,.txt"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-bold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 mx-auto max-w-xs mb-4"
      />

      {error && <p className="text-red-500 text-sm mb-4 font-medium">{error}</p>}

      <Button 
        onClick={handleUpload} 
        disabled={!file || loading} 
        loading={loading}
        className="min-w-[200px]"
      >
        {loading ? "Parsing with AI..." : "Upload & Autofill"}
      </Button>
    </div>
  );
}
