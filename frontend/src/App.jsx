import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import CandidatePipeline from "./apps/recruiter/pages/CandidatePipeline";
import JobCreate from "./apps/recruiter/pages/JobCreate";
import RecruiterConsole from "./apps/recruiter/pages/RecruiterConsole";
import EmployeeConsole from "./apps/employee/pages/EmployeeConsole";
import CandidateProfile from "./pages/CandidateProfile";
import DashboardRouter from "./pages/DashboardRouter";
import LoginHub from "./pages/LoginHub";
import MatchHubPage from "./pages/MatchHubPage";
import TalentOSLanding from "./pages/TalentOSLanding";
import MatchPage from "./pages/MatchPage";
import TaxonomyPage from "./pages/TaxonomyPage";
import Upload from "./pages/Upload";
import { clearAuthToken, getAuthToken, getClientApiKey, getCurrentPrincipal, setClientApiKey } from "./services/api";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [apiKey, setApiKey] = useState(getClientApiKey());
  const hasAuthToken = Boolean(getAuthToken());
  const principalQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasAuthToken
  });

  const saveApiKey = () => {
    setClientApiKey(apiKey.trim());
    setApiKey(getClientApiKey());
  };

  const clearApiKey = () => {
    setClientApiKey("");
    setApiKey("");
  };

  const logout = () => {
    clearAuthToken();
    navigate("/");
    window.location.reload();
  };

  const dashboardLabel = principalQuery.data?.role === "recruiter" ? "Recruiter Dashboard" : principalQuery.data?.role === "employee" ? "Employee Dashboard" : "Dashboard";
  const role = principalQuery.data?.role || "";
  const navItems = getNavItems(role);
  const isPublicMarketingPage = location.pathname === "/" || location.pathname === "/login";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(168,230,207,0.45),_transparent_28%),linear-gradient(180deg,_#f8fbff_0%,_#eef4f8_100%)]">
      {!isPublicMarketingPage ? (
      <header className="sticky top-0 z-20 border-b border-white/60 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <Link to="/" className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black tracking-[0.3em] text-white">
              G
            </div>
            <div>
              <p className="font-display text-2xl font-bold text-slate-950">GARUDA</p>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sky-700">
                {role === "recruiter" ? "Recruiter Workspace" : role === "employee" ? "Employee Workspace" : "TalentOS Platform"}
              </p>
            </div>
          </Link>
          <div className="flex flex-col gap-3 lg:items-end">
            <nav className="flex flex-wrap gap-3 text-sm font-semibold">
              {navItems.map((item) => (
                <Link key={item.to} to={item.to} className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">
                  {item.label}
                </Link>
              ))}
              {hasAuthToken ? (
                <Link to="/dashboard" className="rounded-full px-4 py-2 text-slate-700 transition hover:bg-slate-100">{dashboardLabel}</Link>
              ) : null}
            </nav>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Paste API key for protected routes"
                className="min-w-[280px] rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm outline-none focus:border-sky-400"
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
                {hasAuthToken ? (
                  <button
                    type="button"
                    onClick={logout}
                    className="rounded-full bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700"
                  >
                    Logout
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </header>
      ) : null}
      <main className={isPublicMarketingPage ? "" : "mx-auto max-w-7xl px-6 py-10"}>
        <Routes>
          <Route path="/" element={<TalentOSLanding />} />
          <Route path="/login" element={<LoginHub />} />
          <Route path="/resume/upload" element={<Upload />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/dashboard" element={<DashboardRouter />} />
          <Route path="/candidates/:candidateId" element={<CandidateProfile />} />
          <Route path="/match" element={<MatchHubPage />} />
          <Route path="/match/:candidateId" element={<MatchPage />} />
          <Route path="/taxonomy" element={<TaxonomyPage />} />
          <Route path="/talentos/recruiter" element={<RecruiterConsole />} />
          <Route path="/talentos/recruiter/jobs/new" element={<JobCreate />} />
          <Route path="/talentos/recruiter/jobs/:jobId/pipeline" element={<CandidatePipeline />} />
          <Route path="/talentos/employee" element={<EmployeeConsole />} />
        </Routes>
      </main>
    </div>
  );
}

function getNavItems(role) {
  if (role === "recruiter") {
    return [
      { to: "/", label: "Home" },
      { to: "/talentos/recruiter", label: "Workspace" },
      { to: "/talentos/recruiter/jobs/new", label: "Create Job" },
      { to: "/match", label: "Pipelines" }
    ];
  }

  if (role === "employee") {
    return [
      { to: "/", label: "Home" },
      { to: "/talentos/employee", label: "Workspace" },
      { to: "/resume/upload", label: "Resume Lab" },
      { to: "/taxonomy", label: "Taxonomy" }
    ];
  }

  return [
    { to: "/", label: "Home" },
    { to: "/resume/upload", label: "Resume Lab" },
    { to: "/match", label: "Match" },
    { to: "/taxonomy", label: "Taxonomy" },
    { to: "/talentos/recruiter", label: "Recruiter" },
    { to: "/talentos/employee", label: "Employee" }
  ];
}
