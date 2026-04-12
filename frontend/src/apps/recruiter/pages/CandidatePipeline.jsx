import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getAuthToken, getRecruiterCandidates, getRecruiterJob, runRecruiterMatching, updateRecruiterCandidateStage } from "../../../services/api";

const STAGES = ["new", "reviewed", "shortlisted", "interview", "offer", "hired", "rejected"];

export default function CandidatePipeline() {
  const { jobId } = useParams();
  const queryClient = useQueryClient();
  const hasRecruiterToken = Boolean(getAuthToken());

  if (!hasRecruiterToken) {
    return (
      <section className="rounded-[2rem] bg-white p-10 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-rose-600">Recruiter Auth Required</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Login before opening recruiter pipelines.</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          TalentOS recruiter pages require a JWT bearer token. The old API key box in the header is only for the V2 REST routes.
        </p>
        <div className="mt-6">
          <Link to="/talentos/recruiter" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            Open Recruiter Console
          </Link>
        </div>
      </section>
    );
  }

  const jobQuery = useQuery({
    queryKey: ["recruiter-job", jobId],
    queryFn: () => getRecruiterJob(jobId),
    enabled: Boolean(jobId)
  });

  const candidatesQuery = useQuery({
    queryKey: ["recruiter-candidates", jobId],
    queryFn: () => getRecruiterCandidates(jobId),
    enabled: Boolean(jobId)
  });

  const runMatchingMutation = useMutation({
    mutationFn: () => runRecruiterMatching(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recruiter-candidates", jobId] });
    }
  });

  const stageMutation = useMutation({
    mutationFn: ({ candidateId, stage }) => updateRecruiterCandidateStage(jobId, candidateId, { stage }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recruiter-candidates", jobId] });
    }
  });

  const items = candidatesQuery.data?.items || [];

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Recruiter Pipeline</p>
            <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">
              {jobQuery.data?.title || "Candidate Pipeline"}
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              {jobQuery.data ? `${jobQuery.data.company} • ${jobQuery.data.location_city || "Remote"}` : "Loading job..."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => runMatchingMutation.mutate()}
            className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
          >
            {runMatchingMutation.isPending ? "Running..." : "Run Matching"}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to={`/talentos/recruiter/jobs/${jobId}/forms`} className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
            Open Form Builder
          </Link>
        </div>
        {runMatchingMutation.data ? (
          <p className="mt-4 text-sm text-slate-600">
            Last run matched {runMatchingMutation.data.matched_count} candidates and auto-shortlisted {runMatchingMutation.data.shortlisted_count}.
          </p>
        ) : null}
        {runMatchingMutation.error?.response?.data?.message ? (
          <p className="mt-4 text-sm text-rose-600">{runMatchingMutation.error.response.data.message}</p>
        ) : null}
      </section>

      <section className="overflow-x-auto rounded-[2rem] bg-white p-6 shadow-panel">
        {!items.length ? (
          <div className="mb-6 rounded-[1.5rem] border border-dashed border-slate-300 p-5 text-sm text-slate-600">
            No candidates are in this pipeline yet. If this job was created from a rough pasted JD, recreate it in Manual Mode so the required skills stay exact.
          </div>
        ) : null}
        <div className="grid min-w-[1100px] gap-4 xl:grid-cols-7">
          {STAGES.map((stage) => {
            const stageItems = items.filter((item) => item.pipeline_stage === stage);
            return (
              <div key={stage} className="rounded-[1.5rem] bg-slate-50 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-600">{stage}</h2>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500">{stageItems.length}</span>
                </div>
                <div className="space-y-3">
                  {stageItems.map((candidate) => (
                    <article key={`${stage}-${candidate.candidate_id}`} className="rounded-[1.25rem] bg-white p-4 shadow-sm">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-slate-900">{candidate.candidate_name || candidate.candidate_id}</h3>
                          <p className="text-xs text-slate-500">{candidate.location_label || "Unknown location"}</p>
                        </div>
                        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                          {candidate.grade} {candidate.final_score}
                        </span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(candidate.top_skills || []).slice(0, 3).map((skill) => (
                          <span key={`${candidate.candidate_id}-${skill}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                            {skill}
                          </span>
                        ))}
                      </div>
                      <p className="mt-3 text-xs text-slate-500">
                        {candidate.location_status === "local" ? "Local candidate" : "Relocation candidate"}
                        {candidate.distance_km ? ` • ${candidate.distance_km} km` : ""}
                      </p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {nextStageOptions(stage).map((nextStage) => (
                          <button
                            key={`${candidate.candidate_id}-${nextStage}`}
                            type="button"
                            onClick={() => stageMutation.mutate({ candidateId: candidate.candidate_id, stage: nextStage })}
                            className="rounded-full bg-slate-950 px-3 py-2 text-xs font-semibold text-white"
                          >
                            Move to {nextStage}
                          </button>
                        ))}
                      </div>
                    </article>
                  ))}
                  {!stageItems.length ? (
                    <div className="rounded-[1rem] border border-dashed border-slate-300 p-4 text-xs text-slate-500">
                      No candidates in {stage}.
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function nextStageOptions(stage) {
  const index = STAGES.indexOf(stage);
  if (index === -1) {
    return [];
  }
  return STAGES.slice(index + 1, index + 3);
}
