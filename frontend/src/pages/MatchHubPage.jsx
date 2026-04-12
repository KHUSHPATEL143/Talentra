import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getAuthToken, getCurrentPrincipal, listRecruiterJobs } from "../services/api";

export default function MatchHubPage() {
  const hasToken = Boolean(getAuthToken());
  const meQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasToken
  });
  const jobsQuery = useQuery({
    queryKey: ["recruiter-jobs"],
    queryFn: listRecruiterJobs,
    enabled: meQuery.data?.role === "recruiter"
  });

  if (meQuery.data?.role === "recruiter") {
    const jobs = jobsQuery.data?.items || [];
    return (
      <div className="space-y-6">
        <section className="rounded-[2rem] bg-white p-8 shadow-panel">
          <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Recruiter Matching</p>
          <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Run matching against your posted jobs.</h1>
          <p className="mt-4 text-sm text-slate-600">
            The Match tab now acts as a recruiter job launcher. Pick one of your roles to open its pipeline and run ranking.
          </p>
        </section>
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => (
            <article key={job.id} className="rounded-[2rem] bg-white p-6 shadow-panel">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{job.company}</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">{job.title}</h2>
              <p className="mt-2 text-sm text-slate-600">
                {[job.location_city, job.location_state, job.location_country].filter(Boolean).join(", ") || "Remote"}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {(job.required_skills || []).slice(0, 4).map((skill) => (
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
            <section className="rounded-[2rem] bg-white p-8 shadow-panel">
              <h2 className="font-display text-2xl font-bold text-slate-900">No posted jobs yet.</h2>
              <p className="mt-3 text-sm text-slate-600">Create a recruiter role first, then this tab will show it here.</p>
              <div className="mt-6">
                <Link to="/talentos/recruiter/jobs/new" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                  Create Job
                </Link>
              </div>
            </section>
          ) : null}
        </section>
      </div>
    );
  }

  return (
    <section className="rounded-[2rem] bg-white p-8 shadow-panel">
      <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Match Hub</p>
      <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">TalentOS matching now starts from posted jobs.</h1>
      <p className="mt-4 max-w-2xl text-sm text-slate-600">
        Recruiters should login first and then use this tab to open one of their jobs. The old resume-vs-JD playground is still available through the Resume Lab flow.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/talentos/recruiter" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
          Recruiter Login
        </Link>
        <Link to="/resume/upload" className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700">
          Open Resume Lab
        </Link>
      </div>
    </section>
  );
}
