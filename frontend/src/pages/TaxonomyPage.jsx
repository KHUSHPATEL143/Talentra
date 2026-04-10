import { useQuery } from "@tanstack/react-query";
import TaxonomyBrowser from "../components/TaxonomyBrowser";
import { getTaxonomyStats } from "../services/api";

export default function TaxonomyPage() {
  const statsQuery = useQuery({
    queryKey: ["taxonomy-stats"],
    queryFn: getTaxonomyStats
  });

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Canonical Skill Graph</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Browse the national-scale taxonomy that powers normalization.</h1>
      </section>
      <TaxonomyBrowser stats={statsQuery.data} />
    </div>
  );
}
