import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getPublicIntakeForm, submitPublicIntakeForm } from "../../../services/api";

export default function PublicApplyForm() {
  const { slug } = useParams();
  const formQuery = useQuery({
    queryKey: ["public-form", slug],
    queryFn: () => getPublicIntakeForm(slug),
    enabled: Boolean(slug),
  });
  const submitMutation = useMutation({
    mutationFn: (payload) => submitPublicIntakeForm(slug, payload),
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    submitMutation.mutate({
      name: String(formData.get("name") || ""),
      email: String(formData.get("email") || ""),
      phone: String(formData.get("phone") || ""),
      location: String(formData.get("location") || ""),
      open_to_relocation: formData.get("open_to_relocation") === "on",
      github_url: String(formData.get("github_url") || ""),
      linkedin_url: String(formData.get("linkedin_url") || ""),
      answers: Object.fromEntries((formQuery.data?.fields || []).map((field) => [field.key, formData.get(field.key)])),
    });
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Public Application</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Apply through TalentOS</h1>
        <p className="mt-4 text-sm text-slate-600">Share your core details and extra answers for this recruiter-managed role.</p>
      </section>
      <form onSubmit={handleSubmit} className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="grid gap-4">
          <Input name="name" label="Name" />
          <Input name="email" label="Email" type="email" />
          <Input name="phone" label="Phone" />
          <Input name="location" label="Location" />
          <Input name="github_url" label="GitHub URL" />
          <Input name="linkedin_url" label="LinkedIn URL" />
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" name="open_to_relocation" />
            Open to relocation
          </label>
          {(formQuery.data?.fields || []).map((field) => (
            <Input key={field.key} name={field.key} label={field.label} />
          ))}
          {submitMutation.data ? <p className="text-sm text-emerald-700">Application submitted successfully.</p> : null}
          {submitMutation.error?.response?.data?.message ? <p className="text-sm text-rose-600">{submitMutation.error.response.data.message}</p> : null}
          <button type="submit" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            {submitMutation.isPending ? "Submitting..." : "Submit Application"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Input({ label, ...props }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</span>
      <input {...props} required className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400" />
    </label>
  );
}
