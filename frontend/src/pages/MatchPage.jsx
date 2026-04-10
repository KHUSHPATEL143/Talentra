import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import GapAnalysisPanel from "../components/GapAnalysisPanel";
import MatchScoreGauge from "../components/MatchScoreGauge";
import { matchCandidate } from "../services/api";

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
      </section>

      <section className="space-y-6">
        <MatchScoreGauge score={result?.score || 0} grade={result?.grade || "F"} />
        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <h2 className="text-lg font-bold text-slate-900">Matched Skills</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {(result?.matched_skills || []).map((item) => (
              <div key={`${item.skill}-${item.confidence}`} className="rounded-2xl bg-slate-100 px-4 py-3">
                <p className="font-semibold text-slate-900">{item.skill}</p>
                <p className="text-xs text-slate-500">Confidence {item.confidence} • {item.candidate_years} yrs</p>
              </div>
            ))}
          </div>
        </div>
        <GapAnalysisPanel missing_skills={result?.missing_skills || []} />
        <div className="rounded-3xl bg-white p-6 shadow-panel">
          <h2 className="text-lg font-bold text-slate-900">Recommendations</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
            {(result?.recommendations || []).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>
    </div>
  );
}
