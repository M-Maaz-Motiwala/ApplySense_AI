"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "../../../lib/auth";
import { Button } from "../../../components/ui/Button";
import { InputField } from "../../../components/ui/InputField";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    const payload = {
      name: email.split("@")[0], // default name
      email,
      password,
      experience_blocks: {
        education: [],
        coursework: [],
        experience: [],
        projects: [],
        linkedin: "",
        github: ""
      },
      skills_matrix: {
        languages: [],
        tools: [],
        frameworks: []
      }
    };

    const res = await register(payload);
    
    if (res?.error) {
      setError(res.error);
      setLoading(false);
    } else {
      router.push("/dashboard");
      router.refresh();
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-300">
        <div className="p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Create an Account</h1>
            <p className="text-slate-500 mt-2 text-sm">Start your automated job application journey</p>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-50 border border-red-100 text-red-600 text-sm font-semibold rounded-lg text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <InputField label="Email Address" type="email" name="email" required />
            <InputField label="Password" type="password" name="password" required />
            <InputField label="Confirm Password" type="password" name="confirmPassword" required />

            <Button type="submit" variant="primary" className="w-full !mt-8 py-3 text-sm" loading={loading}>
              Create Account
            </Button>
          </form>
        </div>
        
        <div className="bg-slate-50 border-t border-slate-100 p-6 text-center">
          <p className="text-sm font-medium text-slate-600">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-indigo-600 hover:text-indigo-800 font-bold transition-colors">
              Login here
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
