import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import GapAnalysisPanel from "../components/GapAnalysisPanel";
import MatchScoreGauge from "../components/MatchScoreGauge";
import { getApiErrorDetails, matchCandidate } from "../services/api";

export default function MatchPage() {
  const params = useParams();
  const [candidateId, setCandidateId] = useState(params.candidateId || "");
  const [jobDescription, setJobDescription] = useState("");
  const [requiredWeight, setRequiredWeight] = useState(0.7);
  const [preferredWeight, setPreferredWeight] = useState(0.3);
  const [mode, setMode] = useState("precision");

  const normalizedWeights = useMemo(() => {
    const total = requiredWeight + preferredWeight;
    return {
      required: Number((requiredWeight / total).toFixed(2)),
      preferred: Number((preferredWeight / total).toFixed(2))
    };
  }, [requiredWeight, preferredWeight]);

  const matchMutation = useMutation({
    mutationFn: () => matchCandidate(candidateId, jobDescription, normalizedWeights, mode)
  });

  const result = matchMutation.data;
  const matchError = matchMutation.error ? getApiErrorDetails(matchMutation.error) : null;

  return (
    <div className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
      <section className="space-y-6 rounded-[2rem] bg-white p-8 shadow-panel">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-orange-600">Semantic Matching</p>
          <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Score a candidate against a live job description.</h1>
        </div>
        <input
          value={candidateId}
          onChange={(event) => setCandidateId(event.target.value)}
          placeholder="Candidate ID"
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
        />
        <textarea
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
          placeholder="Paste the job description here..."
          rows={14}
          className="w-full rounded-3xl border border-slate-200 px-4 py-4 text-sm outline-none focus:border-sky-400"
        />
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Required Weight: {normalizedWeights.required}
            <input type="range" min="0.1" max="0.9" step="0.05" value={requiredWeight} onChange={(event) => setRequiredWeight(Number(event.target.value))} className="mt-2 w-full" />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Preferred Weight: {normalizedWeights.preferred}
            <input type="range" min="0.1" max="0.9" step="0.05" value={preferredWeight} onChange={(event) => setPreferredWeight(Number(event.target.value))} className="mt-2 w-full" />
          </label>
        </div>
        <div className="flex gap-3">
          {["precision", "recall"].map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setMode(option)}
              className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === option ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              {option}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => matchMutation.mutate()}
          disabled={!candidateId || !jobDescription || matchMutation.isPending}
          className="rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {matchMutation.isPending ? "Scoring..." : "Run Match"}
        </button>
        {matchError ? (
          <div className="rounded-3xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p className="font-semibold">Match request failed</p>
            <p className="mt-1">{matchError.message}</p>
            {matchError.traceId ? <p className="mt-2 text-xs text-red-600">Trace ID: {matchError.traceId}</p> : null}
          </div>
        ) : null}
      </section>

      <section className="space-y-6">
        <MatchScoreGauge score={result?.score || 0} grade={result?.grade || "F"} />
        {!result && !matchMutation.isPending ? (
          <div className="rounded-3xl bg-white p-6 text-sm text-slate-500 shadow-panel">
            Enter a candidate ID and job description, then run the match to see score, parsed requirements, and gap analysis.
          </div>
        ) : null}
        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <h2 className="text-lg font-bold text-slate-900">Matched Skills</h2>
          {(result?.matched_skills || []).length ? (
            <div className="mt-4 flex flex-wrap gap-3">
              {(result?.matched_skills || []).map((item) => (
                <div key={`${item.skill}-${item.confidence}`} className="rounded-2xl bg-slate-100 px-4 py-3">
                  <p className="font-semibold text-slate-900">{item.skill}</p>
                  <p className="text-xs text-slate-500">Confidence {item.confidence} - {item.candidate_years} yrs</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">Matched skills will appear here after the scoring run completes.</p>
          )}
        </div>
        {result ? (
          <div className="rounded-3xl bg-white p-6 shadow-panel">
            <h2 className="text-lg font-bold text-slate-900">Parsed Job Requirements</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Required</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(result.parsed_requirements.required_skills || []).length ? (
                    result.parsed_requirements.required_skills.map((skill) => (
                      <span key={`required-${skill}`} className="rounded-full bg-red-50 px-3 py-2 text-sm font-medium text-red-700">{skill}</span>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500">No required skills were extracted.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Preferred</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(result.parsed_requirements.preferred_skills || []).length ? (
                    result.parsed_requirements.preferred_skills.map((skill) => (
                      <span key={`preferred-${skill}`} className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">{skill}</span>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500">No preferred skills were extracted.</p>
                  )}
                </div>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Experience match: <span className="font-semibold text-slate-900">{result.experience_match}</span>
              {" "}· Minimum years requested: <span className="font-semibold text-slate-900">{result.parsed_requirements.min_experience_years || 0}</span>
              {" "}· Role level: <span className="font-semibold capitalize text-slate-900">{result.parsed_requirements.role_level || "unspecified"}</span>
            </p>
          </div>
        ) : null}
        <GapAnalysisPanel missing_skills={result?.missing_skills || []} />
        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <h2 className="text-lg font-bold text-slate-900">Recommendations</h2>
          {(result?.recommendations || []).length ? (
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
              {(result?.recommendations || []).map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : (
            <p className="mt-4 text-sm text-slate-500">Recommendations will appear once a match result is available.</p>
          )}
        </div>
      </section>
    </div>
  );
}
