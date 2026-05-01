"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { register } from "../../../lib/auth";
import { Button } from "../../../components/ui/Button";
import { InputField } from "../../../components/ui/InputField";
import { TagInput } from "../../../components/ui/TagInput";

const STEPS = ["Account", "Personal", "Preferences", "Skills", "Experience"];

export default function RegisterPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    name: "",
    phone: "",
    location: "",
    experience_years: 0,
    desired_roles: [] as string[],
    desired_domains: [] as string[],
    skills: [] as string[],
    frameworks: [] as string[],
    tools: [] as string[],
    projects: [{ title: "", description: "", technologies: [] as string[] }]
  });

  // Load draft from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("registration_draft");
    if (saved) {
      try {
        setFormData(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse draft");
      }
    }
  }, []);

  // Auto-save draft
  useEffect(() => {
    localStorage.setItem("registration_draft", JSON.stringify(formData));
  }, [formData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === "experience_years" ? Number(value) : value }));
  };

  const handleTags = (name: string, tags: string[]) => {
    setFormData(prev => ({ ...prev, [name]: tags }));
  };

  const handleProjectChange = (index: number, field: string, value: any) => {
    const newProjects = [...formData.projects];
    newProjects[index] = { ...newProjects[index], [field]: value };
    setFormData(prev => ({ ...prev, projects: newProjects }));
  };

  const addProject = () => {
    setFormData(prev => ({
      ...prev,
      projects: [...prev.projects, { title: "", description: "", technologies: [] }]
    }));
  };

  const removeProject = (index: number) => {
    setFormData(prev => ({
      ...prev,
      projects: prev.projects.filter((_, i) => i !== index)
    }));
  };

  const handleNext = () => {
    if (currentStep === 1) {
      if (!formData.email || !formData.password) return setError("Email and password are required");
      if (formData.password !== formData.confirmPassword) return setError("Passwords do not match");
    }
    setError("");
    setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
  };

  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = async () => {
    setLoading(true);
    setError("");

    // Map UI format to backend schema
    const payload = {
      name: formData.name || formData.email.split("@")[0],
      email: formData.email,
      password: formData.password,
      phone: formData.phone,
      location: formData.location,
      experience_years: formData.experience_years,
      desired_roles: formData.desired_roles,
      desired_domains: formData.desired_domains,
      skills: [
        { category: "Languages", items: formData.skills },
        { category: "Frameworks", items: formData.frameworks },
        { category: "Tools", items: formData.tools }
      ].filter(s => s.items.length > 0),
      projects: formData.projects.filter(p => p.title).map(p => ({
        name: p.title,
        description: p.description,
        technologies: p.technologies,
        bullets: p.description.split("\n").filter(b => b.trim())
      }))
    };

    const res = await register(payload);
    
    if (res?.error) {
      setError(res.error);
      setLoading(false);
    } else {
      localStorage.removeItem("registration_draft");
      router.push("/jobs");
      router.refresh();
    }
  };

  return (
    <main className="min-h-[calc(100vh-64px)] py-12 px-4 flex justify-center bg-slate-50">
      <div className="w-full max-w-3xl glass-panel p-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            {STEPS.map((step, i) => (
              <span key={step} className={`text-xs font-bold uppercase ${currentStep > i ? "text-indigo-600" : "text-slate-400"}`}>
                {step}
              </span>
            ))}
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div 
              className="bg-indigo-600 h-full transition-all duration-300 ease-in-out" 
              style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
            />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 mb-6">Step {currentStep}: {STEPS[currentStep - 1]}</h1>
        {error && <div className="bg-red-50 text-red-600 p-3 rounded-md mb-6 border border-red-200 text-sm font-medium">{error}</div>}

        <div className="min-h-[300px]">
          {/* STEP 1 */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-in">
              <InputField label="Email Address" type="email" name="email" value={formData.email} onChange={handleChange} required />
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Password" type="password" name="password" value={formData.password} onChange={handleChange} required />
                <InputField label="Confirm Password" type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} required />
              </div>
            </div>
          )}

          {/* STEP 2 */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-in">
              <InputField label="Full Name" name="name" placeholder="e.g., Jane Doe" value={formData.name} onChange={handleChange} required />
              <div className="grid grid-cols-2 gap-4">
                <InputField label="Phone Number" name="phone" placeholder="+1 234 567 8900" value={formData.phone} onChange={handleChange} />
                <InputField label="Location" name="location" placeholder="New York, NY" value={formData.location} onChange={handleChange} />
              </div>
            </div>
          )}

          {/* STEP 3 */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-in">
              <InputField label="Years of Experience" type="number" name="experience_years" min="0" value={formData.experience_years} onChange={handleChange} />
              <TagInput label="Desired Roles" tags={formData.desired_roles} onChange={(tags) => handleTags("desired_roles", tags)} placeholder="e.g., Software Engineer, Full Stack" />
              <TagInput label="Desired Domains" tags={formData.desired_domains} onChange={(tags) => handleTags("desired_domains", tags)} placeholder="e.g., FinTech, AI, Web3" />
            </div>
          )}

          {/* STEP 4 */}
          {currentStep === 4 && (
            <div className="space-y-4 animate-in">
              <TagInput label="Programming Languages" tags={formData.skills} onChange={(tags) => handleTags("skills", tags)} placeholder="Python, JavaScript..." />
              <TagInput label="Frameworks" tags={formData.frameworks} onChange={(tags) => handleTags("frameworks", tags)} placeholder="React, Next.js, Django..." />
              <TagInput label="Tools & Infrastructure" tags={formData.tools} onChange={(tags) => handleTags("tools", tags)} placeholder="Docker, AWS, Git..." />
            </div>
          )}

          {/* STEP 5 */}
          {currentStep === 5 && (
            <div className="space-y-6 animate-in">
              <p className="text-sm text-slate-500 mb-4">Add your key projects to provide context for cover letters.</p>
              {formData.projects.map((proj, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg bg-slate-50 relative">
                  {idx > 0 && (
                    <button onClick={() => removeProject(idx)} className="absolute top-3 right-3 text-red-500 hover:text-red-700 font-bold text-sm">Remove</button>
                  )}
                  <InputField label={`Project ${idx + 1} Title`} value={proj.title} onChange={(e) => handleProjectChange(idx, "title", e.target.value)} placeholder="e.g., E-commerce Platform" />
                  <div className="w-full mb-4">
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5 uppercase">Description / Bullets (One per line)</label>
                    <textarea 
                      className="w-full bg-white border border-slate-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px]"
                      value={proj.description}
                      onChange={(e) => handleProjectChange(idx, "description", e.target.value)}
                      placeholder="- Built a scalable backend using...&#10;- Reduced latency by 40%..."
                    />
                  </div>
                  <TagInput label="Technologies Used" tags={proj.technologies} onChange={(tags) => handleProjectChange(idx, "technologies", tags)} placeholder="React, Node.js..." />
                </div>
              ))}
              <Button variant="secondary" onClick={addProject} className="w-full border-dashed border-2">+ Add Another Project</Button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between mt-8 pt-6 border-t border-slate-200">
          <Button variant="ghost" onClick={handleBack} disabled={currentStep === 1 || loading}>
            Back
          </Button>
          
          {currentStep < STEPS.length ? (
            <Button variant="primary" onClick={handleNext}>
              Next Step &rarr;
            </Button>
          ) : (
            <Button variant="primary" onClick={handleSubmit} loading={loading}>
              Complete Registration
            </Button>
          )}
        </div>
      </div>
    </main>
  );
}
