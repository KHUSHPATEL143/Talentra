import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { createIntakeForm, getApiErrorDetails, getAuthToken, getIntakeForm, getIntakeFormResponses, getRecruiterJob } from "../../../services/api";

const DEFAULT_FIELDS = [
  { key: "notice_period", label: "Notice Period", field_type: "text", required: false, options: [] },
  { key: "portfolio", label: "Portfolio URL", field_type: "text", required: false, options: [] },
  { key: "relocation_ready", label: "Open to relocation", field_type: "yes_no", required: false, options: [] },
];

export default function IntakeFormBuilder() {
  const { jobId } = useParams();
  const queryClient = useQueryClient();
  const hasRecruiterToken = Boolean(getAuthToken());
  const jobQuery = useQuery({
    queryKey: ["recruiter-job", jobId],
    queryFn: () => getRecruiterJob(jobId),
    enabled: Boolean(jobId) && hasRecruiterToken,
    retry: false,
  });
  const formQuery = useQuery({
    queryKey: ["intake-form", jobId],
    queryFn: () => getIntakeForm(jobId),
    enabled: Boolean(jobId) && hasRecruiterToken && jobQuery.isSuccess,
    retry: false,
  });
  const saveMutation = useMutation({
    mutationFn: (payload) => createIntakeForm(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intake-form", jobId] });
    },
  });

  const handleCreate = () => {
    saveMutation.mutate({ fields: DEFAULT_FIELDS });
  };

  const form = saveMutation.data || formQuery.data;
  const responsesQuery = useQuery({
    queryKey: ["intake-form-responses", form?.id],
    queryFn: () => getIntakeFormResponses(form.id),
    enabled: Boolean(form?.id) && hasRecruiterToken,
  });
  const publicUrl = form?.public_slug ? `${window.location.origin}/apply/${form.public_slug}` : "";
  const visibleFields = form?.fields || DEFAULT_FIELDS;
  const jobError = jobQuery.error ? getApiErrorDetails(jobQuery.error) : null;
  const loadError = formQuery.error ? getApiErrorDetails(formQuery.error) : null;
  const saveError = saveMutation.error ? getApiErrorDetails(saveMutation.error) : null;

  if (!hasRecruiterToken) {
    return (
      <section className="rounded-[2rem] bg-white p-10 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-rose-600">Recruiter Auth Required</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Login before creating a public intake form.</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          This page uses recruiter JWT auth. Open the recruiter workspace, sign in again, and then come back to this job form.
        </p>
        <div className="mt-6">
          <Link to="/talentos/recruiter" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            Open Recruiter Console
          </Link>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Intake Form</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Recruiter form builder</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          This creates a shareable public intake form for the job. The current version ships with a practical default field set for demo use.
        </p>
        {jobQuery.isFetching ? (
          <div className="mt-6 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
            Verifying this recruiter job before loading the public form...
          </div>
        ) : null}
        {jobQuery.data ? (
          <div className="mt-6 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Job</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{jobQuery.data.title}</p>
            <p className="mt-1 text-sm text-slate-600">{jobQuery.data.company}</p>
          </div>
        ) : null}
        {jobError ? (
          <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 p-5">
            <p className="text-sm font-semibold text-rose-800">Job not available</p>
            <p className="mt-2 text-sm text-rose-700">
              {jobError.message || "This recruiter job could not be found for your current account."}
            </p>
            <p className="mt-2 text-sm text-rose-700">
              Open the job again from your recruiter workspace and then create the intake form from that fresh pipeline link.
            </p>
          </div>
        ) : null}
        {formQuery.isFetching && !form ? (
          <div className="mt-6 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
            Checking whether this job already has a saved public form...
          </div>
        ) : null}
        {loadError && !jobError ? (
          <div className="mt-6 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-semibold text-amber-800">No saved form found yet</p>
            <p className="mt-2 text-sm text-amber-700">
              This job does not have a public application form yet. Click <strong>Create Form</strong> to generate one now.
            </p>
          </div>
        ) : null}
        {saveError ? (
          <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 p-5">
            <p className="text-sm font-semibold text-rose-800">Form save failed</p>
            <p className="mt-2 text-sm text-rose-700">{saveError.message}</p>
          </div>
        ) : null}
        {form?.id ? (
          <div className="mt-6 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-5">
            <p className="text-sm font-semibold text-emerald-800">Form created</p>
            <p className="mt-2 text-sm text-emerald-700">
              This job already has a public intake form. Candidates can apply using the link below.
            </p>
            <div className="mt-4 rounded-2xl bg-white px-4 py-3 text-sm text-slate-700">
              {publicUrl}
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <a
                href={publicUrl}
                target="_blank"
                rel="noreferrer"
                className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
              >
                Open Public Form
              </a>
              <button
                type="button"
                onClick={() => navigator.clipboard.writeText(publicUrl)}
                className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700"
              >
                Copy Link
              </button>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-semibold text-amber-800">No form created yet</p>
            <p className="mt-2 text-sm text-amber-700">
              Click <strong>Create Form</strong> once to generate and save a public application link for this job.
            </p>
          </div>
        )}
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleCreate}
            disabled={saveMutation.isPending || !jobQuery.data}
            className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
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
        <h2 className="font-display text-2xl font-bold text-slate-900">
          {form ? "Configured Fields" : "Default Fields Preview"}
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          {form
            ? "These fields are already saved in the public intake form for this job."
            : "These are the default fields that will be created when you click Create Form."}
        </p>
        <div className="mt-5 grid gap-3">
          {visibleFields.map((field) => (
            <div key={field.key} className="rounded-2xl border border-slate-200 p-4">
              <p className="font-semibold text-slate-900">{field.label}</p>
              <p className="mt-1 text-sm text-slate-600">{field.field_type} - {field.required ? "required" : "optional"}</p>
            </div>
          ))}
        </div>
        {form?.public_slug ? (
          <p className="mt-5 text-sm text-slate-600">
            Public link: <span className="font-mono">{publicUrl}</span>
          </p>
        ) : null}
      </section>

      {form?.id ? (
        <section className="rounded-[2rem] bg-white p-8 shadow-panel">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Responses</p>
              <h2 className="mt-2 font-display text-2xl font-bold text-slate-900">Recent form submissions</h2>
            </div>
            <span className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
              {responsesQuery.data?.total || 0} received
            </span>
          </div>
          {responsesQuery.isLoading ? (
            <div className="mt-6 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
              Loading public form responses...
            </div>
          ) : null}
          {!responsesQuery.isLoading && !(responsesQuery.data?.items || []).length ? (
            <div className="mt-6 rounded-[1.5rem] border border-dashed border-slate-300 p-5 text-sm text-slate-600">
              No candidate has submitted this form yet.
            </div>
          ) : null}
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {(responsesQuery.data?.items || []).map((item) => (
              <article key={item.form_response_id} className="rounded-[1.5rem] border border-slate-200 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">{item.candidate_name || "New applicant"}</h3>
                    <p className="mt-1 text-sm text-slate-600">{item.email || "Email unavailable"}</p>
                    <p className="mt-1 text-sm text-slate-500">{item.location || "Unknown location"}</p>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                    {item.pipeline_stage}
                  </span>
                </div>
                <p className="mt-3 text-sm text-slate-600">Match score {item.match_score}</p>
                <div className="mt-4 space-y-2 text-sm text-slate-600">
                  {Object.entries(item.response_preview || {}).slice(0, 3).map(([key, value]) => (
                    <div key={`${item.form_response_id}-${key}`} className="rounded-2xl bg-slate-50 px-4 py-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{key}</p>
                      <p className="mt-1 text-sm text-slate-700">{String(value)}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <Link to={`/talentos/recruiter/jobs/${jobId}/pipeline`} className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
                    Open Pipeline
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
