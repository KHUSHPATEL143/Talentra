import PropTypes from "prop-types";
import { useState } from "react";

function categoryTone(category) {
  if (category === "Soft Skills") return "bg-fuchsia-100 text-fuchsia-700";
  if (category === "Domain") return "bg-emerald-100 text-emerald-700";
  if (category === "Emerging") return "bg-amber-100 text-amber-700";
  return "bg-sky-100 text-sky-700";
}

function proficiencyDot(level) {
  return {
    beginner: "bg-slate-400",
    intermediate: "bg-sky-500",
    advanced: "bg-emerald-500",
    expert: "bg-amber-500"
  }[level] || "bg-slate-400";
}

export default function SkillCard({ skill }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <button
      type="button"
      onClick={() => setExpanded((current) => !current)}
      className="w-full rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-panel"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={`h-3 w-3 rounded-full ${proficiencyDot(skill.proficiency)}`} />
          <span className="font-semibold text-slate-900">{skill.name}</span>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${categoryTone(skill.category)}`}>
          {skill.category}
        </span>
      </div>
      {expanded ? (
        <div className="mt-4 space-y-2 text-sm text-slate-600">
          <p>Proficiency: <span className="font-semibold capitalize text-slate-900">{skill.proficiency}</span></p>
          <p>Aliases: {skill.aliases?.length ? skill.aliases.join(", ") : "No aliases listed"}</p>
          <p>Category: {skill.category} / {skill.subcategory}</p>
          <p>Inference: {skill.inferred ? "Inferred from supporting skills" : "Directly observed in the resume"}</p>
          <p>Emerging: {skill.emerging ? "Queued for taxonomy review" : "Canonical taxonomy skill"}</p>
        </div>
      ) : null}
    </button>
  );
}

SkillCard.propTypes = {
  skill: PropTypes.shape({
    name: PropTypes.string.isRequired,
    proficiency: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    subcategory: PropTypes.string,
    aliases: PropTypes.arrayOf(PropTypes.string),
    inferred: PropTypes.bool,
    emerging: PropTypes.bool
  }).isRequired
};
