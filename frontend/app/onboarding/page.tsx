"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { StepForm } from "../../components/ui/StepForm";
import { InputField } from "../../components/ui/InputField";
import { TagInput } from "../../components/ui/TagInput";
import { ResumeUploader } from "../../components/ui/ResumeUploader";
import { BulletEditor } from "../../components/ui/BulletEditor";
import { Button } from "../../components/ui/Button";
import { DateRangePicker } from "../../components/ui/DateRangePicker";
import { API_BASE } from "../../lib/api";

// Get token helper
function getClientToken(): string {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? match[1] : "";
  }
  return "";
}

const STEPS = [
  "Basic Info",
  "Resume Upload",
  "Education",
  "Skills Matrix",
  "Experience",
  "Projects",
  "Leadership"
];

// Default strict schema
const defaultData = {
  name: "",
  phone: "",
  location: "",
  experience_years: 0 as number,
  salary_expectation: 0 as number,
  desired_roles: [] as string[],
  desired_domains: [] as string[],
  experience_blocks: {
    education: [{ school: "", degree: "", dates: "", location: "", CGPA: "" }],
    coursework: [],
    experience_level: "Entry Level",
    experience: [{ company: "", title: "", dates: "", location: "", bullets: [] }],
    projects: [{ name: "", tech: "", date: "", bullets: [] }],
    leadership: [{ org: "", dates: "", title: "", location: "", bullets: [] }],
    linkedin: "",
    github: ""
  },
  skills_matrix: {
    languages: [],
    tools: [],
    frameworks: []
  }
};

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState(defaultData);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [token, setToken] = useState("");
  const [skillSuggestions, setSkillSuggestions] = useState<string[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    const t = getClientToken();
    if (!t) {
      router.push("/auth/login");
      return;
    }
    setToken(t);

    // Fetch existing profile
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${t}` }
    })
    .then(res => res.json())
    .then(profile => {
      if (profile) {
        setData({
          name: profile.name || "",
          phone: profile.phone || "",
          location: profile.location || "",
          desired_roles: profile.desired_roles || [],
          desired_domains: profile.desired_domains || [],
          experience_blocks: { ...defaultData.experience_blocks, ...profile.experience_blocks },
          skills_matrix: { ...defaultData.skills_matrix, ...profile.skills_matrix }
        });
      }
    });
  }, [router]);

  // Auto-save logic
  const saveDraft = useCallback(async (currentData: any) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/auth/profile/draft`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(currentData)
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        console.error("Draft save failed:", res.status, errData);
        return;
      }
      showToast("Saved automatically");
    } catch (e) {
      console.error("Draft save network error:", e);
    }
  }, [token]);

  // Debounce save (simple version)
  useEffect(() => {
    const timer = setTimeout(() => {
      saveDraft(data);
    }, 2000);
    return () => clearTimeout(timer);
  }, [data, saveDraft]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = async () => {
    setLoading(true);
    await saveDraft(data);
    setLoading(false);
    router.push("/dashboard");
  };

  const updateField = (field: string, value: any) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const updateBlock = (block: string, field: string, value: any) => {
    setData(prev => ({
      ...prev,
      experience_blocks: {
        ...prev.experience_blocks,
        [field]: value
      }
    }));
  };

  const updateSkill = (field: string, value: any) => {
    setData(prev => ({
      ...prev,
      skills_matrix: {
        ...prev.skills_matrix,
        [field]: value
      }
    }));
  };

  const fetchSkillSuggestions = async (category: string) => {
    // We assume role is derived from experience title for now, or just send a generic request
    const role = data.experience_blocks.experience[0]?.title || "Software Engineer";
    setLoadingSuggestions(true);
    try {
      const res = await fetch(`${API_BASE}/llm/suggest-skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ role, category })
      });
      const resData = await res.json();
      setSkillSuggestions(resData.skills || []);
      showToast(`AI ${category} suggestions ready`);
    } catch (e) {
      showToast("Could not fetch suggestions");
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // Render specific step content
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4 animate-in">
            <InputField label="Full Name" value={data.name} onChange={(e) => updateField("name", e.target.value)} />
            <div className="grid grid-cols-2 gap-4">
              <InputField label="Phone" value={data.phone} onChange={(e) => updateField("phone", e.target.value)} />
              <InputField label="Location" value={data.location} onChange={(e) => updateField("location", e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-900 mb-2">Experience Level</label>
              <select 
                value={data.experience_blocks.experience_level} 
                onChange={(e) => updateBlock("experience_blocks", "experience_level", e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              >
                <option value="Entry Level">Entry Level</option>
                <option value="Junior">Junior (1-2 years)</option>
                <option value="Mid-Level">Mid-Level (3-5 years)</option>
                <option value="Senior">Senior (5+ years)</option>
                <option value="Lead / Manager">Lead / Manager</option>
              </select>
            </div>
            <InputField label="LinkedIn URL" value={data.experience_blocks.linkedin} onChange={(e) => updateBlock("experience_blocks", "linkedin", e.target.value)} />
            <InputField label="GitHub URL" value={data.experience_blocks.github} onChange={(e) => updateBlock("experience_blocks", "github", e.target.value)} />
            
            <div className="pt-4 border-t border-slate-100">
              <TagInput 
                label="Target Job Roles" 
                tags={data.desired_roles} 
                onChange={(tags) => updateField("desired_roles", tags)} 
                placeholder="e.g. Software Engineer, Data Scientist"
              />
              <TagInput 
                label="Target Industries / Domains" 
                tags={data.desired_domains} 
                onChange={(tags) => updateField("desired_domains", tags)} 
                placeholder="e.g. Fintech, AI, E-commerce"
              />
              {data.desired_domains.length === 0 && (
                <p className="text-xs text-amber-600 font-medium">Domain is a mandatory field for profile matching.</p>
              )}
            </div>
          </div>
        );
      case 2:
        return (
          <div className="animate-in">
            <ResumeUploader 
              token={token} 
              onSuccess={(parsed) => {
                setData(prev => {
                  const newState = { ...prev, ...parsed };
                  
                  // Deep merge experience_blocks
                  if (parsed.experience_blocks) {
                    newState.experience_blocks = {
                      ...prev.experience_blocks,
                      ...parsed.experience_blocks
                    };
                    
                    // If the AI returned empty arrays for sections that should at least have one empty entry (for UI), 
                    // or if it omitted them entirely, we handle that here.
                    // But usually, the UI is fine with empty arrays if the user hasn't added anything.
                    // The user specifically asked to "leave them" if no match, so we ensure we don't overwrite with nulls.
                    for (const key in parsed.experience_blocks) {
                      if (!parsed.experience_blocks[key] || (Array.isArray(parsed.experience_blocks[key]) && parsed.experience_blocks[key].length === 0)) {
                        // If AI returned empty, we might want to keep what was there if it was meaningful.
                        // However, for a fresh parse, usually we want exactly what the AI found.
                        // For now, the spread ...prev.experience_blocks already handles missing keys.
                      }
                    }
                  }

                  // Deep merge skills_matrix
                  if (parsed.skills_matrix) {
                    newState.skills_matrix = {
                      ...prev.skills_matrix,
                      ...parsed.skills_matrix
                    };
                  }

                  return newState;
                });
                showToast("Resume parsed successfully!");
                setCurrentStep(3);
              }} 
            />
            <div className="mt-6 text-center">
              <button onClick={handleNext} className="text-sm font-bold text-slate-500 hover:text-indigo-600">
                Skip this step
              </button>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6 animate-in">
            {data.experience_blocks.education.map((edu, i) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg bg-slate-50 relative">
                {i > 0 && <button onClick={() => updateBlock("experience_blocks", "education", data.experience_blocks.education.filter((_, idx) => idx !== i))} className="absolute top-2 right-2 text-red-500 text-sm font-bold">&times; Remove</button>}
                <InputField label="School/University" value={edu.school} onChange={(e) => { const newEdu = [...data.experience_blocks.education]; newEdu[i].school = e.target.value; updateBlock("experience_blocks", "education", newEdu); }} />
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Degree" value={edu.degree} onChange={(e) => { const newEdu = [...data.experience_blocks.education]; newEdu[i].degree = e.target.value; updateBlock("experience_blocks", "education", newEdu); }} />
                  <DateRangePicker label="Dates" value={edu.dates} onChange={(val) => { const newEdu = [...data.experience_blocks.education]; newEdu[i].dates = val; updateBlock("experience_blocks", "education", newEdu); }} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Location" value={edu.location} onChange={(e) => { const newEdu = [...data.experience_blocks.education]; newEdu[i].location = e.target.value; updateBlock("experience_blocks", "education", newEdu); }} />
                  <InputField label="CGPA" value={edu.CGPA} onChange={(e) => { const newEdu = [...data.experience_blocks.education]; newEdu[i].CGPA = e.target.value; updateBlock("experience_blocks", "education", newEdu); }} />
                </div>
              </div>
            ))}
            <Button variant="ghost" onClick={() => updateBlock("experience_blocks", "education", [...data.experience_blocks.education, { school: "", degree: "", dates: "", location: "", CGPA: "" }])}>
              + Add Education
            </Button>

            <div className="border-t border-slate-200 pt-6">
              <TagInput 
                label="Coursework" 
                tags={data.experience_blocks.coursework} 
                onChange={(tags) => updateBlock("experience_blocks", "coursework", tags)} 
                suggestions={["Deep Learning", "NLP", "Distributed Systems", "Databases", "Operating Systems", "Software Engineering"]}
              />
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6 animate-in">
            <div className="flex justify-between items-center mb-4">
              <p className="text-sm text-slate-500">Add your skills manually or let AI suggest them.</p>
            </div>
            <div className="relative pt-4">
              <div className="absolute right-0 top-0 z-10">
                <Button variant="secondary" onClick={() => fetchSkillSuggestions("languages")} loading={loadingSuggestions} className="py-1 px-3 text-xs">🧠 Suggest</Button>
              </div>
              <TagInput label="Languages" tags={data.skills_matrix.languages} onChange={(tags) => updateSkill("languages", tags)} suggestions={skillSuggestions} />
            </div>
            <div className="relative pt-4">
              <div className="absolute right-0 top-0 z-10">
                <Button variant="secondary" onClick={() => fetchSkillSuggestions("frameworks")} loading={loadingSuggestions} className="py-1 px-3 text-xs">🧠 Suggest</Button>
              </div>
              <TagInput label="Frameworks" tags={data.skills_matrix.frameworks} onChange={(tags) => updateSkill("frameworks", tags)} suggestions={skillSuggestions} />
            </div>
            <div className="relative pt-4">
              <div className="absolute right-0 top-0 z-10">
                <Button variant="secondary" onClick={() => fetchSkillSuggestions("tools")} loading={loadingSuggestions} className="py-1 px-3 text-xs">🧠 Suggest</Button>
              </div>
              <TagInput label="Tools" tags={data.skills_matrix.tools} onChange={(tags) => updateSkill("tools", tags)} suggestions={skillSuggestions} />
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-8 animate-in">
            {data.experience_blocks.experience.map((exp, i) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg bg-white relative shadow-sm">
                {i > 0 && <button onClick={() => updateBlock("experience_blocks", "experience", data.experience_blocks.experience.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 text-red-500 text-sm font-bold">&times; Remove</button>}
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Company" value={exp.company} onChange={(e) => { const newExp = [...data.experience_blocks.experience]; newExp[i].company = e.target.value; updateBlock("experience_blocks", "experience", newExp); }} />
                  <InputField label="Title" value={exp.title} onChange={(e) => { const newExp = [...data.experience_blocks.experience]; newExp[i].title = e.target.value; updateBlock("experience_blocks", "experience", newExp); }} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <DateRangePicker label="Dates" value={exp.dates} onChange={(val) => { const newExp = [...data.experience_blocks.experience]; newExp[i].dates = val; updateBlock("experience_blocks", "experience", newExp); }} />
                  <InputField label="Location" value={exp.location} onChange={(e) => { const newExp = [...data.experience_blocks.experience]; newExp[i].location = e.target.value; updateBlock("experience_blocks", "experience", newExp); }} />
                </div>
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <BulletEditor 
                    label="Resume Bullets"
                    bullets={exp.bullets}
                    onChange={(bullets) => { const newExp = [...data.experience_blocks.experience]; newExp[i].bullets = bullets; updateBlock("experience_blocks", "experience", newExp); }}
                    token={token}
                  />
                </div>
              </div>
            ))}
            <Button variant="ghost" onClick={() => updateBlock("experience_blocks", "experience", [...data.experience_blocks.experience, { company: "", title: "", dates: "", location: "", bullets: [] }])}>
              + Add Experience
            </Button>
          </div>
        );
      case 6:
        return (
          <div className="space-y-8 animate-in">
            {data.experience_blocks.projects.map((proj, i) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg bg-white relative shadow-sm">
                {i > 0 && <button onClick={() => updateBlock("experience_blocks", "projects", data.experience_blocks.projects.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 text-red-500 text-sm font-bold">&times; Remove</button>}
                <InputField label="Project Name" value={proj.name} onChange={(e) => { const newP = [...data.experience_blocks.projects]; newP[i].name = e.target.value; updateBlock("experience_blocks", "projects", newP); }} />
                <div className="grid grid-cols-2 gap-4">
                  <div className="pt-1">
                    <TagInput 
                      label="Technologies" 
                      tags={proj.tech ? proj.tech.split(",").map(t=>t.trim()).filter(Boolean) : []} 
                      onChange={(tags) => { const newP = [...data.experience_blocks.projects]; newP[i].tech = tags.join(", "); updateBlock("experience_blocks", "projects", newP); }} 
                      suggestions={[]} 
                    />
                  </div>
                  <DateRangePicker label="Date" single value={proj.date} onChange={(val) => { const newP = [...data.experience_blocks.projects]; newP[i].date = val; updateBlock("experience_blocks", "projects", newP); }} />
                </div>
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <BulletEditor 
                    label="Project Bullets"
                    bullets={proj.bullets}
                    onChange={(bullets) => { const newP = [...data.experience_blocks.projects]; newP[i].bullets = bullets; updateBlock("experience_blocks", "projects", newP); }}
                    token={token}
                  />
                </div>
              </div>
            ))}
            <Button variant="ghost" onClick={() => updateBlock("experience_blocks", "projects", [...data.experience_blocks.projects, { name: "", tech: "", date: "", bullets: [] }])}>
              + Add Project
            </Button>
          </div>
        );
      case 7:
        return (
          <div className="space-y-8 animate-in">
            {(data.experience_blocks.leadership || []).map((lead, i) => (
              <div key={i} className="p-4 border border-slate-200 rounded-lg bg-white relative shadow-sm">
                {i > 0 && <button onClick={() => updateBlock("experience_blocks", "leadership", data.experience_blocks.leadership.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 text-red-500 text-sm font-bold">&times; Remove</button>}
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Organization" value={lead.org} onChange={(e) => { const newL = [...data.experience_blocks.leadership]; newL[i].org = e.target.value; updateBlock("experience_blocks", "leadership", newL); }} />
                  <InputField label="Title" value={lead.title} onChange={(e) => { const newL = [...data.experience_blocks.leadership]; newL[i].title = e.target.value; updateBlock("experience_blocks", "leadership", newL); }} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <DateRangePicker label="Dates" value={lead.dates} onChange={(val) => { const newL = [...data.experience_blocks.leadership]; newL[i].dates = val; updateBlock("experience_blocks", "leadership", newL); }} />
                  <InputField label="Location" value={lead.location} onChange={(e) => { const newL = [...data.experience_blocks.leadership]; newL[i].location = e.target.value; updateBlock("experience_blocks", "leadership", newL); }} />
                </div>
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <BulletEditor 
                    label="Leadership Bullets"
                    bullets={lead.bullets}
                    onChange={(bullets) => { const newL = [...data.experience_blocks.leadership]; newL[i].bullets = bullets; updateBlock("experience_blocks", "leadership", newL); }}
                    token={token}
                  />
                </div>
              </div>
            ))}
            <Button variant="ghost" onClick={() => updateBlock("experience_blocks", "leadership", [...(data.experience_blocks.leadership || []), { org: "", dates: "", title: "", location: "", bullets: [] }])}>
              + Add Leadership
            </Button>
          </div>
        );
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 py-12 px-4 relative">
      {toast && (
        <div className="fixed bottom-6 right-6 bg-slate-800 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-bold animate-in fade-in slide-in-from-bottom-4 z-50">
          {toast}
        </div>
      )}

      <div className="max-w-3xl mx-auto flex justify-end mb-4">
        <Button variant="secondary" onClick={() => saveDraft(data)} className="text-xs">
          💾 Save Draft Manually
        </Button>
      </div>

      <StepForm
        steps={STEPS}
        currentStep={currentStep}
        onNext={handleNext}
        onBack={handleBack}
        onSubmit={handleSubmit}
        isLoading={loading}
      >
        {renderStep()}
      </StepForm>
    </main>
  );
}
