import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import SkillCard from "../components/SkillCard";
import {
  getApiErrorDetails,
  getCachedParseResult,
  getCandidate,
  getCandidateSkills
} from "../services/api";

const tabs = ["Overview", "Skills", "Experience", "Education", "Raw JSON"];

export default function CandidateProfile() {
  const { candidateId } = useParams();
  const location = useLocation();
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
  const parseResult = useMemo(
    () => location.state?.parseResult || getCachedParseResult(candidateId),
    [candidateId, location.state]
  );
  const candidateError = candidateQuery.error ? getApiErrorDetails(candidateQuery.error) : null;
  const skillsError = skillsQuery.error ? getApiErrorDetails(skillsQuery.error) : null;
  const traceErrors = (parseResult?.traces || []).filter((trace) => trace.error);
  const topProjects = (candidate?.projects || []).slice(0, 4);

  if (candidateQuery.isLoading || skillsQuery.isLoading) {
    return (
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Candidate Profile</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Loading candidate intelligence...</h1>
        <p className="mt-3 text-sm text-slate-500">We’re fetching the structured profile and normalized skills now.</p>
      </section>
    );
  }

  if ((candidateError && !candidate) || (skillsError && !skillProfile)) {
    return (
      <section className="rounded-[2rem] border border-red-200 bg-red-50 p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-red-600">Candidate Profile</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">We couldn’t load this candidate.</h1>
        <p className="mt-3 text-sm text-red-700">{candidateError?.message || skillsError?.message}</p>
        {(candidateError?.traceId || skillsError?.traceId) ? (
          <p className="mt-2 text-xs text-red-600">Trace ID: {candidateError?.traceId || skillsError?.traceId}</p>
        ) : null}
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Candidate Profile</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">{candidate?.name || "Candidate profile"}</h1>
        <p className="mt-3 text-sm text-slate-500">{candidate?.summary || "Structured profile details will appear here after parsing completes."}</p>
        <div className="mt-4 flex flex-wrap gap-3 text-xs font-semibold">
          <span className="rounded-full bg-slate-100 px-3 py-2 text-slate-700">Quality {(candidate?.quality_score || 0).toFixed(2)}</span>
          <span className="rounded-full bg-sky-100 px-3 py-2 text-sky-700">{skillProfile?.normalized_skills?.length || 0} normalized skills</span>
          {skillProfile?.emerging_skills?.length ? (
            <span className="rounded-full bg-amber-100 px-3 py-2 text-amber-700">{skillProfile.emerging_skills.length} skills pending review</span>
          ) : null}
        </div>
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

      {parseResult?.partial ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-panel">
          <p className="text-sm font-semibold text-amber-800">Partial parse result</p>
          <p className="mt-1 text-sm text-amber-700">
            This profile was recovered with fallback logic in at least one stage. Review the extracted content before treating it as final.
          </p>
          {traceErrors.length ? (
            <div className="mt-3 space-y-1 text-xs text-amber-700">
              {traceErrors.map((trace) => (
                <p key={`${trace.agent}-${trace.error}`}>{trace.agent}: {trace.error}</p>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {candidateError || skillsError ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 shadow-panel">
          <p className="font-semibold">Some candidate data is unavailable.</p>
          <p className="mt-1">{candidateError?.message || skillsError?.message}</p>
        </section>
      ) : null}

      {activeTab === "Overview" ? (
        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl bg-white p-6 shadow-panel md:col-span-2">
            <h2 className="text-lg font-bold text-slate-900">Profile Overview</h2>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              {candidate?.summary || "No profile overview was extracted from this resume."}
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <OverviewStat
                label="Experience Entries"
                value={String((candidate?.experience || []).length)}
              />
              <OverviewStat
                label="Projects"
                value={String((candidate?.projects || []).length)}
              />
              <OverviewStat
                label="Education Entries"
                value={String((candidate?.education || []).length)}
              />
              <OverviewStat
                label="Skill Highlights"
                value={String((candidate?.skills || []).length)}
              />
            </div>
          </div>
          <div className="rounded-3xl bg-white p-6 shadow-panel">
            <h2 className="text-lg font-bold text-slate-900">Contact & Profiles</h2>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <p>Email: {candidate?.email || "Unavailable"}</p>
              <p>Phone: {candidate?.phone || "Unavailable"}</p>
              <p>LinkedIn: <ProfileLink href={candidate?.linkedin} label={candidate?.linkedin} /></p>
              <p>GitHub: <ProfileLink href={candidate?.github} label={candidate?.github} /></p>
              <p>Location: {[candidate?.location?.city, candidate?.location?.country].filter(Boolean).join(", ") || "Unavailable"}</p>
            </div>
          </div>
          <div className="rounded-3xl bg-white p-6 shadow-panel">
            <h2 className="text-lg font-bold text-slate-900">Highlights</h2>
            {(candidate?.skills || []).length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {(candidate?.skills || []).slice(0, 12).map((skill) => (
                  <span key={skill} className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500">No direct skill highlights were extracted from this resume.</p>
            )}
          </div>
          <div className="rounded-3xl bg-white p-6 shadow-panel md:col-span-2">
            <h2 className="text-lg font-bold text-slate-900">Top Projects</h2>
            {topProjects.length ? (
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                {topProjects.map((project, index) => (
                  <article key={`${project.name}-${index}`} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-semibold text-slate-900">{project.name || "Untitled project"}</h3>
                      {project.url ? (
                        <a
                          href={project.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"
                        >
                          Open
                        </a>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {project.description || "No project description was extracted from this resume."}
                    </p>
                    {(project.technologies || []).length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(project.technologies || []).slice(0, 6).map((tech) => (
                          <span key={`${project.name}-${tech}`} className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
                            {tech}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500">No projects were extracted for this candidate.</p>
            )}
          </div>
        </section>
      ) : null}

      {activeTab === "Skills" ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(skillProfile?.normalized_skills || []).length ? (
            (skillProfile?.normalized_skills || []).map((skill) => (
              <SkillCard key={`${skill.name}-${skill.source_skill}`} skill={skill} />
            ))
          ) : (
            <div className="rounded-3xl bg-white p-6 text-sm text-slate-500 shadow-panel">
              No normalized skills are available for this candidate yet.
            </div>
          )}
        </section>
      ) : null}

      {activeTab === "Experience" ? (
        <section className="space-y-4">
          {(candidate?.experience || []).length ? (
            (candidate?.experience || []).map((item, index) => (
              <div key={`${item.company}-${index}`} className="rounded-3xl bg-white p-6 shadow-panel">
                <h3 className="text-lg font-bold text-slate-900">{item.role} @ {item.company}</h3>
                <p className="mt-1 text-sm text-slate-500">{item.start} - {item.end}</p>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
                  {(item.responsibilities || []).map((responsibility) => <li key={responsibility}>{responsibility}</li>)}
                </ul>
              </div>
            ))
          ) : (
            <div className="rounded-3xl bg-white p-6 text-sm text-slate-500 shadow-panel">No experience entries were extracted.</div>
          )}
        </section>
      ) : null}

      {activeTab === "Education" ? (
        <section className="space-y-4">
          {(candidate?.education || []).length ? (
            (candidate?.education || []).map((item, index) => (
              <div key={`${item.institution}-${index}`} className="rounded-3xl bg-white p-6 shadow-panel">
                <h3 className="text-lg font-bold text-slate-900">{item.degree} in {item.field}</h3>
                <p className="mt-1 text-sm text-slate-500">{item.institution} - {item.year}</p>
              </div>
            ))
          ) : (
            <div className="rounded-3xl bg-white p-6 text-sm text-slate-500 shadow-panel">No education entries were extracted.</div>
          )}
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

function ProfileLink({ href, label }) {
  if (!href) {
    return "Unavailable";
  }
  return (
    <a href={href} target="_blank" rel="noreferrer" className="break-all text-sky-700 hover:text-sky-900 hover:underline">
      {label || href}
    </a>
  );
}

function OverviewStat({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
