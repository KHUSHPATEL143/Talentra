import { Link, Route, Routes } from "react-router-dom";
import CandidateProfile from "./pages/CandidateProfile";
import MatchPage from "./pages/MatchPage";
import TaxonomyPage from "./pages/TaxonomyPage";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-white/60 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="font-display text-2xl font-bold text-slate-950">
            GARUDA
          </Link>
          <nav className="flex gap-3 text-sm font-semibold">
            <Link to="/" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Upload</Link>
            <Link to="/match" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Match</Link>
            <Link to="/taxonomy" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Taxonomy</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/candidates/:candidateId" element={<CandidateProfile />} />
          <Route path="/match" element={<MatchPage />} />
          <Route path="/match/:candidateId" element={<MatchPage />} />
          <Route path="/taxonomy" element={<TaxonomyPage />} />
        </Routes>
      </main>
    </div>
  );
}
