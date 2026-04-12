import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createRecruiterJob, getAuthToken } from "../../../services/api";

export default function JobCreate() {
  const navigate = useNavigate();
  const hasRecruiterToken = Boolean(getAuthToken());
  const [mode, setMode] = useState("manual");
  const createMutation = useMutation({
    mutationFn: createRecruiterJob,
    onSuccess: (data) => navigate(`/talentos/recruiter/jobs/${data.id}/pipeline`)
  });

  if (!hasRecruiterToken) {
    return (
      <section className="rounded-[2rem] bg-white p-10 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-rose-600">Recruiter Auth Required</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Login before creating a TalentOS role.</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          This page uses recruiter JWT auth, not the V2 API key field in the header. Open the recruiter console,
          register or login once, and then come back here.
        </p>
        <div className="mt-6">
          <Link to="/talentos/recruiter" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            Open Recruiter Console
          </Link>
        </div>
      </section>
    );
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const rawJd = formData.get("raw_jd")?.toString() || "";
    const title = formData.get("title")?.toString() || "";
    const location_city = formData.get("location_city")?.toString() || "";
    const company = formData.get("company")?.toString() || "";
    const requiredSkills = (formData.get("required_skills")?.toString() || "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean)
      .map((skill) => ({ skill, min_years: 1, weight: 1.0 }));

    const payload = mode === "paste"
      ? { raw_jd: rawJd }
      : {
          structured: {
            title,
            company,
            description: formData.get("description")?.toString() || "",
            location_city,
            location_state: formData.get("location_state")?.toString() || "",
            location_country: formData.get("location_country")?.toString() || "India",
            remote: formData.get("remote") === "on",
            hybrid: formData.get("hybrid") === "on",
            accept_relocation: formData.get("accept_relocation") !== null,
            employment_type: formData.get("employment_type")?.toString() || "full_time",
            experience_min: Number(formData.get("experience_min") || 0),
            experience_max: Number(formData.get("experience_max") || 0) || null,
            salary_min: Number(formData.get("salary_min") || 0) || null,
            salary_max: Number(formData.get("salary_max") || 0) || null,
            currency: formData.get("currency")?.toString() || "INR",
            required_skills: requiredSkills,
            preferred_skills: [],
            auto_shortlist_threshold: Number(formData.get("auto_shortlist_threshold") || 70),
            radius_km: Number(formData.get("radius_km") || 50)
          }
        };

    createMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">TalentOS Recruiter</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Create a location-aware role</h1>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setMode("manual")}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "manual" ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
          >
            Manual Mode
          </button>
          <button
            type="button"
            onClick={() => setMode("paste")}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "paste" ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
          >
            Paste JD Mode
          </button>
        </div>
      </section>

      <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2rem] bg-white p-8 shadow-panel">
          <h2 className="font-display text-2xl font-bold text-slate-900">Paste JD</h2>
          <textarea
            name="raw_jd"
            rows={16}
            placeholder="Paste a freeform job description here and TalentOS will structure it."
            className="mt-4 w-full rounded-[1.5rem] border border-slate-200 px-4 py-4 text-sm outline-none focus:border-sky-400"
          />
          <p className="mt-3 text-xs text-slate-500">
            Paste JD mode uses the left text box only. Manual mode uses the structured fields on the right.
          </p>
        </section>

        <section className="rounded-[2rem] bg-white p-8 shadow-panel">
          <h2 className="font-display text-2xl font-bold text-slate-900">Or fill key fields manually</h2>
          <div className="mt-4 grid gap-4">
            <Input name="title" label="Role Title" />
            <Input name="company" label="Company" />
            <Input name="description" label="Summary" as="textarea" rows={4} />
            <Input name="location_city" label="City" />
            <Input name="location_state" label="State" />
            <Input name="location_country" label="Country" defaultValue="India" />
            <Input name="required_skills" label="Required Skills" placeholder="React, TypeScript, Tailwind" />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input name="experience_min" label="Min Experience" type="number" defaultValue="2" />
              <Input name="radius_km" label="Radius (km)" type="number" defaultValue="50" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input name="salary_min" label="Salary Min" type="number" />
              <Input name="salary_max" label="Salary Max" type="number" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input name="currency" label="Currency" defaultValue="INR" />
              <Input name="auto_shortlist_threshold" label="Auto-shortlist Threshold" type="number" defaultValue="70" />
            </div>
            <label className="flex items-center gap-3 text-sm text-slate-700">
              <input type="checkbox" name="accept_relocation" defaultChecked />
              Accept relocation candidates
            </label>
            <label className="flex items-center gap-3 text-sm text-slate-700">
              <input type="checkbox" name="remote" />
              Remote role
            </label>
            {createMutation.error?.response?.data?.message ? (
              <p className="text-sm text-rose-600">{createMutation.error.response.data.message}</p>
            ) : null}
            <button type="submit" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
              {createMutation.isPending ? "Creating..." : mode === "paste" ? "Create Job From JD" : "Create Manual Job"}
            </button>
            <p className="text-xs text-slate-500">After creating the job, open the form builder to create a public intake link.</p>
          </div>
        </section>
      </form>
    </div>
  );
}

function Input({ label, as, ...props }) {
  const Component = as === "textarea" ? "textarea" : "input";
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</span>
      <Component
        {...props}
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
      />
    </label>
  );
}
