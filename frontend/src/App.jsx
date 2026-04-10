import { useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import CandidateProfile from "./pages/CandidateProfile";
import MatchPage from "./pages/MatchPage";
import TaxonomyPage from "./pages/TaxonomyPage";
import Upload from "./pages/Upload";
import { getClientApiKey, setClientApiKey } from "./services/api";

export default function App() {
  const [apiKey, setApiKey] = useState(getClientApiKey());

  const saveApiKey = () => {
    setClientApiKey(apiKey.trim());
    setApiKey(getClientApiKey());
  };

  const clearApiKey = () => {
    setClientApiKey("");
    setApiKey("");
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-white/60 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <Link to="/" className="font-display text-2xl font-bold text-slate-950">
            GARUDA
          </Link>
          <div className="flex flex-col gap-3 lg:items-end">
            <nav className="flex gap-3 text-sm font-semibold">
              <Link to="/" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Upload</Link>
              <Link to="/match" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Match</Link>
              <Link to="/taxonomy" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">Taxonomy</Link>
            </nav>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Paste API key for protected routes"
                className="min-w-[280px] rounded-full border border-slate-200 bg-white px-4 py-2 text-sm outline-none focus:border-sky-400"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={saveApiKey}
                  className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white"
                >
                  Save Key
                </button>
                <button
                  type="button"
                  onClick={clearApiKey}
                  className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
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
