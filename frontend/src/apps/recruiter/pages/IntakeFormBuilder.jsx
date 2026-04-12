import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { createIntakeForm, getIntakeForm } from "../../../services/api";

const DEFAULT_FIELDS = [
  { key: "notice_period", label: "Notice Period", field_type: "text", required: false, options: [] },
  { key: "portfolio", label: "Portfolio URL", field_type: "text", required: false, options: [] },
  { key: "relocation_ready", label: "Open to relocation", field_type: "yes_no", required: false, options: [] },
];

export default function IntakeFormBuilder() {
  const { jobId } = useParams();
  const formQuery = useQuery({
    queryKey: ["intake-form", jobId],
    queryFn: () => getIntakeForm(jobId),
    enabled: Boolean(jobId),
    retry: false,
  });
  const saveMutation = useMutation({
    mutationFn: (payload) => createIntakeForm(jobId, payload),
  });

  const handleCreate = () => {
    saveMutation.mutate({ fields: DEFAULT_FIELDS });
  };

  const form = saveMutation.data || formQuery.data;

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Intake Form</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Recruiter form builder</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          This creates a shareable public intake form for the job. The current version ships with a practical default field set for demo use.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button type="button" onClick={handleCreate} className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            {saveMutation.isPending ? "Saving..." : form ? "Replace Form" : "Create Form"}
          </button>
          {form?.public_slug ? (
            <Link to={`/apply/${form.public_slug}`} className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700">
              Open Public Form
            </Link>
          ) : null}
        </div>
      </section>

      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <h2 className="font-display text-2xl font-bold text-slate-900">Configured Fields</h2>
        <div className="mt-5 grid gap-3">
          {(form?.fields || DEFAULT_FIELDS).map((field) => (
            <div key={field.key} className="rounded-2xl border border-slate-200 p-4">
              <p className="font-semibold text-slate-900">{field.label}</p>
              <p className="mt-1 text-sm text-slate-600">{field.field_type} {field.required ? "· required" : "· optional"}</p>
            </div>
          ))}
        </div>
        {form?.public_slug ? (
          <p className="mt-5 text-sm text-slate-600">
            Public link: <span className="font-mono">/apply/{form.public_slug}</span>
          </p>
        ) : null}
      </section>
    </div>
  );
}
