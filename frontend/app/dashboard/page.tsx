import Link from "next/link";
import { getToken } from "../../lib/auth";
import { API_BASE } from "../../lib/api";
import { RefreshJobsButton } from "../../components/ui/RefreshJobsButton";

async function getProfile(token: string) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!res.ok) return null;
  return res.json();
}

function calculateCompletion(profile: any) {
  if (!profile) return 0;
  let score = 0;
  if (profile.name && profile.name !== profile.email.split('@')[0]) score += 10;
  if (profile.phone) score += 10;
  if (profile.location) score += 10;
  
  const blocks = profile.experience_blocks || {};
  if (blocks.linkedin || blocks.github) score += 10;
  if (blocks.education?.length > 0) score += 20;
  if (blocks.experience?.length > 0) score += 20;
  
  const skills = profile.skills_matrix || {};
  if (skills.languages?.length > 0 || skills.tools?.length > 0) score += 20;
  
  return score;
}

export default async function DashboardPage() {
  const token = await getToken();
  const profile = await getProfile(token);
  const completion = calculateCompletion(profile);

  return (
    <main className="py-8 animate-in">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900">Welcome, {profile?.name || "User"}! 👋</h1>
        <p className="text-slate-500 mt-2">Manage your profile, resumes, and automated applications.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Profile Completion Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Profile Completion</h2>
            <div className="w-full bg-slate-200 h-3 rounded-full mb-4 overflow-hidden">
              <div 
                className={`h-full ${completion === 100 ? 'bg-emerald-500' : 'bg-indigo-600'}`} 
                style={{ width: `${completion}%` }}
              />
            </div>
            <p className="text-slate-600 mb-6">
              Your profile is <span className="font-bold text-slate-900">{completion}%</span> complete. 
              {completion < 100 ? " Complete your profile to get the best AI-generated resumes." : " You are ready to apply!"}
            </p>
          </div>
          
          <div className="flex gap-4">
            <Link href="/onboarding" className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-6 rounded-lg text-sm transition-colors text-center flex-1">
              {completion === 0 ? "Start Profile Builder" : completion >= 90 ? "Edit Profile" : "Complete Profile"}
            </Link>
          </div>
        </div>

        {/* Quick Actions Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Quick Actions</h2>
          <div className="space-y-4">
            <RefreshJobsButton token={token} />
            <Link href="/jobs" className="block p-4 border border-slate-100 rounded-lg hover:border-indigo-200 hover:bg-indigo-50 transition-colors group">
              <div className="flex items-center gap-3">
                <span className="text-2xl">💼</span>
                <div>
                  <h3 className="font-bold text-slate-900 group-hover:text-indigo-700">Browse Jobs</h3>
                  <p className="text-sm text-slate-500">Find roles and calculate match scores.</p>
                </div>
              </div>
            </Link>
            <Link href="/applications" className="block p-4 border border-slate-100 rounded-lg hover:border-emerald-200 hover:bg-emerald-50 transition-colors group">
              <div className="flex items-center gap-3">
                <span className="text-2xl">📄</span>
                <div>
                  <h3 className="font-bold text-slate-900 group-hover:text-emerald-700">My Applications</h3>
                  <p className="text-sm text-slate-500">Review AI-generated cover letters.</p>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
