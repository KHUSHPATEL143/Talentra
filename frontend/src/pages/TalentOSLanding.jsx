import { Link } from "react-router-dom";

export default function TalentOSLanding() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.7),_rgba(244,244,239,1)_52%),linear-gradient(180deg,_#fcfcf8_0%,_#f0f2eb_100%)] px-6 py-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <section className="rounded-[2.75rem] border border-stone-200/70 bg-white/85 p-10 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="max-w-4xl">
            <p className="text-xs font-semibold uppercase tracking-[0.42em] text-stone-500">GARUDA by TalentOS</p>
            <h1 className="mt-6 font-display text-6xl font-bold leading-[0.98] text-slate-950">
              A calmer, sharper way to understand hiring fit.
            </h1>
            <p className="mt-8 max-w-3xl text-lg leading-9 text-slate-600">
              GARUDA turns resumes, skills, projects, and location context into a cleaner hiring signal. Recruiters get focused ranking instead of resume noise. Candidates get a richer profile than a one-page PDF can carry.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/login" className="rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white">
                Enter Platform
              </Link>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <article className="rounded-[2.5rem] border border-stone-200/70 bg-white/80 p-8 shadow-[0_16px_50px_rgba(15,23,42,0.06)]">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-stone-500">What It Does</p>
            <div className="mt-6 grid gap-5">
              <FeatureRow
                title="Role-aware ranking"
                body="Every candidate is evaluated against the exact role, not a generic static score."
              />
              <FeatureRow
                title="Project-backed signal"
                body="Profiles surface work evidence, top projects, and stronger skill context beyond keyword matching."
              />
              <FeatureRow
                title="Location intelligence"
                body="Recruiters can prioritize local talent, relocation-ready candidates, and role-specific fit."
              />
            </div>
          </article>

          <article className="rounded-[2.5rem] border border-stone-200/70 bg-[linear-gradient(180deg,_#111827_0%,_#1f2937_100%)] p-8 text-white shadow-[0_16px_50px_rgba(15,23,42,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-stone-300">Product Flow</p>
            <div className="mt-6 space-y-5">
              <FlowStep number="01" text="A recruiter defines a role with location, requirements, and hiring intent." />
              <FlowStep number="02" text="GARUDA parses resumes and profiles into structured candidate intelligence." />
              <FlowStep number="03" text="The platform ranks candidates with clearer fit, gaps, and evidence." />
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}

function FeatureRow({ title, body }) {
  return (
    <div className="rounded-[1.75rem] bg-stone-50/80 p-5">
      <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
    </div>
  );
}

function FlowStep({ number, text }) {
  return (
    <div className="flex gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-sm font-semibold text-stone-200">
        {number}
      </div>
      <p className="pt-2 text-sm leading-7 text-slate-200">{text}</p>
    </div>
  );
}
