import PropTypes from "prop-types";
import { useEffect, useMemo, useState } from "react";
import { getTaxonomy } from "../services/api";

function groupTaxonomy(items) {
  return items.reduce((accumulator, item) => {
    accumulator[item.category] = accumulator[item.category] || {};
    accumulator[item.category][item.subcategory] = accumulator[item.category][item.subcategory] || [];
    accumulator[item.category][item.subcategory].push(item);
    return accumulator;
  }, {});
}

export default function TaxonomyBrowser({ stats }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function loadAll() {
      let page = 1;
      let aggregated = [];
      let total = Infinity;
      while (aggregated.length < total) {
        const data = await getTaxonomy({ page, page_size: 100 });
        aggregated = aggregated.concat(data.items);
        total = data.total;
        page += 1;
      }
      if (mounted) {
        setItems(aggregated);
      }
    }
    loadAll();
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const needle = search.toLowerCase();
    return items.filter((item) =>
      item.canonical_name.toLowerCase().includes(needle) ||
      item.aliases.some((alias) => alias.toLowerCase().includes(needle)) ||
      item.category.toLowerCase().includes(needle) ||
      item.subcategory.toLowerCase().includes(needle)
    );
  }, [items, search]);

  const grouped = useMemo(() => groupTaxonomy(filtered), [filtered]);

  return (
    <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="rounded-3xl bg-white p-6 shadow-panel">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold text-slate-900">Skill Taxonomy</h2>
            <p className="text-sm text-slate-500">Explore canonical skills, aliases, and category structure.</p>
          </div>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search taxonomy..."
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none ring-0 focus:border-sky-400"
          />
        </div>
        <div className="mt-6 max-h-[60vh] space-y-5 overflow-y-auto pr-2">
          {Object.entries(grouped).map(([category, subcategories]) => (
            <div key={category}>
              <h3 className="text-lg font-bold text-slate-900">{category}</h3>
              <div className="mt-3 space-y-3">
                {Object.entries(subcategories).map(([subcategory, skills]) => (
                  <details key={subcategory} className="rounded-2xl border border-slate-200 p-4" open>
                    <summary className="cursor-pointer font-semibold text-slate-700">{subcategory}</summary>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {skills.map((skill) => (
                        <button
                          type="button"
                          key={skill.id}
                          onClick={() => setSelected(skill)}
                          className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-sky-100 hover:text-sky-700"
                        >
                          {skill.canonical_name}
                        </button>
                      ))}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-3xl bg-slate-950 p-6 text-slate-50 shadow-panel">
        <h3 className="font-display text-2xl font-bold">Taxonomy Snapshot</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <div className="rounded-2xl bg-white/10 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-slate-300">Skills</p>
            <p className="mt-2 text-3xl font-bold">{stats?.total_skills || items.length}</p>
          </div>
          <div className="rounded-2xl bg-white/10 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-slate-300">Categories</p>
            <p className="mt-2 text-3xl font-bold">{stats?.category_count || Object.keys(grouped).length}</p>
          </div>
          <div className="rounded-2xl bg-white/10 p-4">
            <p className="text-xs uppercase tracking-[0.25em] text-slate-300">Pending Review</p>
            <p className="mt-2 text-3xl font-bold">{stats?.pending_review_count || 0}</p>
          </div>
        </div>

        <div className="mt-6 rounded-3xl bg-white/10 p-5">
          <h4 className="text-lg font-semibold">{selected?.canonical_name || "Select a skill"}</h4>
          <div className="mt-3 space-y-2 text-sm text-slate-200">
            <p>Aliases: {selected?.aliases?.join(", ") || "Choose a skill in the tree to inspect aliases."}</p>
            <p>Path: {selected ? `${selected.category} / ${selected.subcategory}` : "Waiting for selection"}</p>
            <p>Proficiency distribution: Live candidate distribution becomes richer as parsed candidates accumulate in the platform.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

TaxonomyBrowser.propTypes = {
  stats: PropTypes.shape({
    total_skills: PropTypes.number,
    category_count: PropTypes.number,
    pending_review_count: PropTypes.number
  })
};

TaxonomyBrowser.defaultProps = {
  stats: null
};
