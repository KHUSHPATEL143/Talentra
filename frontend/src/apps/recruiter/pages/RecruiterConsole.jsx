import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getAuthToken, getCurrentPrincipal, listRecruiterJobs, login, registerRecruiter, setAuthToken } from "../../../services/api";

export default function RecruiterConsole() {
  const hasRecruiterToken = Boolean(getAuthToken());
  const meQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasRecruiterToken
  });
  const jobsQuery = useQuery({
    queryKey: ["recruiter-jobs"],
    queryFn: listRecruiterJobs,
    enabled: meQuery.data?.role === "recruiter"
  });

  const registerMutation = useMutation({
    mutationFn: registerRecruiter,
    onSuccess: (_, variables) => {
      loginMutation.mutate({
        email: variables.email,
        password: variables.password
      });
    }
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      window.location.reload();
    }
  });

  const jobs = jobsQuery.data?.items || [];

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-[2rem] bg-[linear-gradient(135deg,_#0f172a_0%,_#1d4ed8_100%)] p-8 text-white shadow-panel">
          <p className="text-sm uppercase tracking-[0.3em] text-emerald-200">TalentOS V3</p>
          <h1 className="mt-3 font-display text-4xl font-bold">Recruiter Command Center</h1>
          <p className="mt-4 max-w-2xl text-sm text-slate-300">
            Post a role, run location-aware matching, and move candidates across the pipeline with explainable scores.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/talentos/recruiter/jobs/new" className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">
              Create Job
            </Link>
          </div>
        </div>
        <div className="rounded-[2rem] bg-white p-8 shadow-panel">
          <h2 className="font-display text-2xl font-bold text-slate-900">Access</h2>
          {meQuery.data?.role === "recruiter" || hasRecruiterToken ? (
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <p>{meQuery.data?.email ? `Logged in as ${meQuery.data.email}` : "Recruiter token is stored in this browser."}</p>
              <p>JWT auth is active for TalentOS recruiter routes.</p>
            </div>
          ) : (
            <div className="mt-4 space-y-6">
              <AuthForm
                title="Register"
                fields={[
                  { name: "name", label: "Name" },
                  { name: "email", label: "Email", type: "email" },
                  { name: "password", label: "Password", type: "password" },
                  { name: "company_name", label: "Company" }
                ]}
                buttonLabel={registerMutation.isPending ? "Creating..." : "Create Recruiter"}
                error={registerMutation.error?.response?.data?.message || ""}
                onSubmit={(payload) => registerMutation.mutate(payload)}
              />
              <AuthForm
                title="Login"
                fields={[
                  { name: "email", label: "Email", type: "email" },
                  { name: "password", label: "Password", type: "password" }
                ]}
                buttonLabel={loginMutation.isPending ? "Signing in..." : "Login"}
                error={loginMutation.error?.response?.data?.message || ""}
                onSubmit={(payload) => loginMutation.mutate(payload)}
              />
            </div>
          )}
        </div>
      </section>

      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Jobs</p>
            <h2 className="mt-2 font-display text-3xl font-bold text-slate-900">Your active recruiter roles</h2>
          </div>
          {jobsQuery.isFetching ? <span className="text-sm text-slate-500">Refreshing...</span> : null}
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => (
            <article key={job.id} className="rounded-[1.5rem] border border-slate-200 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{job.company}</p>
              <h3 className="mt-2 text-xl font-semibold text-slate-900">{job.title}</h3>
              <p className="mt-2 text-sm text-slate-600">
                {[job.location_city, job.location_state, job.location_country].filter(Boolean).join(", ") || "Remote"}
              </p>
              <p className="mt-3 text-sm text-slate-600">Threshold {job.auto_shortlist_threshold}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {(job.required_skills || []).slice(0, 3).map((skill) => (
                  <span key={`${job.id}-${skill.skill}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    {skill.skill}
                  </span>
                ))}
              </div>
              <div className="mt-5 flex gap-3">
                <Link to={`/talentos/recruiter/jobs/${job.id}/pipeline`} className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                  Open Pipeline
                </Link>
              </div>
            </article>
          ))}
          {!jobs.length && !jobsQuery.isLoading ? (
            <div className="rounded-[1.5rem] border border-dashed border-slate-300 p-6 text-sm text-slate-500">
              No recruiter jobs yet. Create the first TalentOS role to start matching candidates.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function AuthForm({ title, fields, buttonLabel, error, onSubmit }) {
  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    onSubmit(Object.fromEntries(formData.entries()));
    event.currentTarget.reset();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-[1.5rem] border border-slate-200 p-4">
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {fields.map((field) => (
        <label key={field.name} className="block">
          <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{field.label}</span>
          <input
            name={field.name}
            type={field.type || "text"}
            required
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
          />
        </label>
      ))}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
        {buttonLabel}
      </button>
    </form>
  );
}
