import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import SkillCard from "../components/SkillCard";
import { getCandidate, getCandidateSkills } from "../services/api";

const tabs = ["Overview", "Skills", "Experience", "Education", "Raw JSON"];

export default function CandidateProfile() {
  const { candidateId } = useParams();
  const [activeTab, setActiveTab] = useState("Overview");
  const candidateQuery = useQuery({
    queryKey: ["candidate", candidateId],
    queryFn: () => getCandidate(candidateId),
    enabled: Boolean(candidateId)
  });
  const skillsQuery = useQuery({
    queryKey: ["candidate-skills", candidateId],
    queryFn: () => getCandidateSkills(candidateId),
    enabled: Boolean(candidateId)
  });

  const rawJson = useMemo(() => JSON.stringify({
    candidate: candidateQuery.data,
    skills: skillsQuery.data
  }, null, 2), [candidateQuery.data, skillsQuery.data]);

  const candidate = candidateQuery.data;
  const skillProfile = skillsQuery.data?.skill_profile;

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Candidate Profile</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">{candidate?.name || "Loading..."}</h1>
        <p className="mt-3 text-sm text-slate-500">{candidate?.summary || "Structured profile details will appear here after parsing completes."}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm font-semibold ${activeTab === tab ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </section>

      {activeTab === "Overview" ? (
        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl bg-white p-6 shadow-panel">
            <h2 className="text-lg font-bold text-slate-900">Contact</h2>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <p>Email: {candidate?.email || "Unavailable"}</p>
              <p>Phone: {candidate?.phone || "Unavailable"}</p>
              <p>LinkedIn: {candidate?.linkedin || "Unavailable"}</p>
              <p>Location: {[candidate?.location?.city, candidate?.location?.country].filter(Boolean).join(", ") || "Unavailable"}</p>
            </div>
          </div>
          <div className="rounded-3xl bg-white p-6 shadow-panel">
            <h2 className="text-lg font-bold text-slate-900">Highlights</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(candidate?.skills || []).slice(0, 12).map((skill) => (
                <span key={skill} className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {activeTab === "Skills" ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(skillProfile?.normalized_skills || []).map((skill) => (
            <SkillCard key={`${skill.name}-${skill.source_skill}`} skill={skill} />
          ))}
        </section>
      ) : null}

      {activeTab === "Experience" ? (
        <section className="space-y-4">
          {(candidate?.experience || []).map((item, index) => (
            <div key={`${item.company}-${index}`} className="rounded-3xl bg-white p-6 shadow-panel">
              <h3 className="text-lg font-bold text-slate-900">{item.role} @ {item.company}</h3>
              <p className="mt-1 text-sm text-slate-500">{item.start} - {item.end}</p>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
                {(item.responsibilities || []).map((responsibility) => <li key={responsibility}>{responsibility}</li>)}
              </ul>
            </div>
          ))}
        </section>
      ) : null}

      {activeTab === "Education" ? (
        <section className="space-y-4">
          {(candidate?.education || []).map((item, index) => (
            <div key={`${item.institution}-${index}`} className="rounded-3xl bg-white p-6 shadow-panel">
              <h3 className="text-lg font-bold text-slate-900">{item.degree} in {item.field}</h3>
              <p className="mt-1 text-sm text-slate-500">{item.institution} • {item.year}</p>
            </div>
          ))}
        </section>
      ) : null}

      {activeTab === "Raw JSON" ? (
        <section className="rounded-3xl bg-slate-950 p-6 text-sm text-slate-100 shadow-panel">
          <pre className="overflow-x-auto whitespace-pre-wrap">{rawJson}</pre>
        </section>
      ) : null}
    </div>
  );
}
