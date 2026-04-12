import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import BatchUploadTable from "../../../components/BatchUploadTable";
import FileDropzone from "../../../components/FileDropzone";
import {
  downloadRecruiterCandidatesCsv,
  getApiErrorDetails,
  getAuthToken,
  getRecruiterCandidates,
  getRecruiterJob,
  queueRecruiterResumeBatch,
  runRecruiterMatching,
  updateRecruiterCandidateStage
} from "../../../services/api";

const STAGES = ["new", "reviewed", "shortlisted", "interview", "offer", "hired", "rejected"];

export default function CandidatePipeline() {
  const { jobId } = useParams();
  const queryClient = useQueryClient();
  const hasRecruiterToken = Boolean(getAuthToken());
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchJobId, setBatchJobId] = useState("");

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

  const exportMutation = useMutation({
    mutationFn: () => downloadRecruiterCandidatesCsv(jobId)
  });

  const batchUploadMutation = useMutation({
    mutationFn: () => queueRecruiterResumeBatch(jobId, batchFiles),
    onSuccess: (data) => {
      setBatchJobId(data.job_id);
      queryClient.invalidateQueries({ queryKey: ["recruiter-candidates", jobId] });
    }
  });

  const items = candidatesQuery.data?.items || [];
  const selectedCandidates = items.filter((item) => selectedCandidateIds.includes(item.candidate_id));
  const batchError = batchUploadMutation.error ? getApiErrorDetails(batchUploadMutation.error) : null;

  const toggleCandidateSelection = (candidateId) => {
    setSelectedCandidateIds((current) => {
      if (current.includes(candidateId)) {
        return current.filter((item) => item !== candidateId);
      }
      if (current.length >= 3) {
        return current;
      }
      return [...current, candidateId];
    });
  };

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
              {jobQuery.data ? `${jobQuery.data.company} - ${jobQuery.data.location_city || "Remote"}` : "Loading job..."}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => exportMutation.mutate()}
              className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700"
            >
              {exportMutation.isPending ? "Exporting..." : "Export CSV"}
            </button>
            <button
              type="button"
              onClick={() => runMatchingMutation.mutate()}
              className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
            >
              {runMatchingMutation.isPending ? "Running..." : "Run Matching"}
            </button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link to={`/talentos/recruiter/jobs/${jobId}/forms`} className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
            Open Form Builder
          </Link>
          <span className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
            Compare up to 3 candidates
          </span>
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

      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-stone-500">Resume Intake</p>
            <h2 className="mt-2 font-display text-2xl font-bold text-slate-900">Bulk recruiter resume upload</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Upload multiple resumes for this job. Each file is parsed in the background, matched to the current role, and added to the pipeline as a resume upload.
            </p>
          </div>
          <button
            type="button"
            disabled={!batchFiles.length || batchUploadMutation.isPending}
            onClick={() => batchUploadMutation.mutate()}
            className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {batchUploadMutation.isPending ? "Queueing..." : "Queue Resume Batch"}
          </button>
        </div>
        <div className="mt-6">
          <FileDropzone multiple onFileAccepted={(files) => setBatchFiles(files)} />
        </div>
        {batchError ? (
          <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">
            <p className="font-semibold">Bulk recruiter upload failed</p>
            <p className="mt-1">{batchError.message}</p>
          </div>
        ) : null}
        <div className="mt-6">
          <BatchUploadTable
            jobId={batchJobId}
            onBatchComplete={() => {
              queryClient.invalidateQueries({ queryKey: ["recruiter-candidates", jobId] });
            }}
          />
        </div>
      </section>

      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Compare View</p>
            <h2 className="mt-2 font-display text-2xl font-bold text-slate-900">Side-by-side candidate comparison</h2>
          </div>
          <button
            type="button"
            onClick={() => setSelectedCandidateIds([])}
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Clear Compare
          </button>
        </div>
        {selectedCandidates.length < 2 ? (
          <div className="mt-6 rounded-[1.5rem] border border-dashed border-slate-300 p-5 text-sm text-slate-600">
            Select at least 2 candidates from the pipeline cards to compare scores, skills, and gap patterns.
          </div>
        ) : (
          <div className="mt-6 grid gap-4 xl:grid-cols-3">
            {selectedCandidates.map((candidate) => (
              <article key={`compare-${candidate.candidate_id}`} className="rounded-[1.5rem] border border-slate-200 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{candidate.candidate_name || candidate.candidate_id}</h3>
                    <p className="mt-1 text-sm text-slate-500">{candidate.location_label || "Unknown location"}</p>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                    {candidate.grade} {candidate.final_score}
                  </span>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <CompareStat label="Skill" value={candidate.score_breakdown?.skill_score || 0} />
                  <CompareStat label="Experience" value={candidate.score_breakdown?.experience_score || 0} />
                  <CompareStat label="Projects" value={candidate.score_breakdown?.project_score || 0} />
                  <CompareStat label="Verification" value={candidate.score_breakdown?.verification_score || 0} />
                </div>
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Top Skills</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(candidate.top_skills || []).slice(0, 6).map((skill) => (
                      <span key={`compare-${candidate.candidate_id}-${skill}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Missing Required</p>
                  <p className="mt-2 text-sm text-slate-600">
                    {(candidate.missing_required || []).length ? candidate.missing_required.join(", ") : "No critical gaps"}
                  </p>
                </div>
                <p className="mt-4 text-sm text-slate-600">{candidate.recommendation}</p>
              </article>
            ))}
          </div>
        )}
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
                  {stageItems.map((candidate) => {
                    const isSelected = selectedCandidateIds.includes(candidate.candidate_id);
                    return (
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
                          {labelForLocationStatus(candidate.location_status)}
                          {candidate.distance_km ? ` - ${candidate.distance_km} km` : ""}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => toggleCandidateSelection(candidate.candidate_id)}
                            className={`rounded-full px-3 py-2 text-xs font-semibold ${
                              isSelected ? "bg-sky-100 text-sky-700" : "border border-slate-300 text-slate-700"
                            }`}
                          >
                            {isSelected ? "Selected" : "Compare"}
                          </button>
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
                    );
                  })}
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

function labelForLocationStatus(status) {
  if (status === "local") {
    return "Local candidate";
  }
  if (status === "remote") {
    return "Remote candidate";
  }
  return "Relocation candidate";
}

function CompareStat({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-bold text-slate-900">{Math.round(value)}</p>
    </div>
  );
}
