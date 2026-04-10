import PropTypes from "prop-types";

export default function GapAnalysisPanel({ missing_skills }) {
  if (!missing_skills?.length) {
    return (
      <div className="rounded-3xl bg-emerald-50 p-6 text-emerald-800 shadow-panel">
        <p className="text-lg font-bold">Great match! No critical gaps.</p>
        <p className="mt-2 text-sm">The candidate covers the high-priority skill set requested by this role.</p>
      </div>
    );
  }

  return (
    <div className="rounded-3xl bg-white p-6 shadow-panel">
      <h3 className="text-lg font-bold text-slate-900">Gap Analysis</h3>
      <div className="mt-4 space-y-3">
        {missing_skills.map((item) => (
          <div key={`${item.skill}-${item.importance}`} className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-slate-900">{item.skill}</span>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.importance === "required" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-700"}`}>
                {item.importance}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{item.upskilling}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

GapAnalysisPanel.propTypes = {
  missing_skills: PropTypes.arrayOf(
    PropTypes.shape({
      skill: PropTypes.string.isRequired,
      importance: PropTypes.string.isRequired,
      upskilling: PropTypes.string.isRequired
    })
  ).isRequired
};
