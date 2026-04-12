import { useQuery } from "@tanstack/react-query";
import { Link, Navigate } from "react-router-dom";
import { getAuthToken, getCurrentPrincipal } from "../services/api";

export default function DashboardRouter() {
  const hasToken = Boolean(getAuthToken());
  const principalQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasToken
  });

  if (!hasToken) {
    return (
      <section className="rounded-[2rem] bg-white p-10 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-rose-600">Sign In Required</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Choose your dashboard after logging in.</h1>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/talentos/recruiter" className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white">
            Recruiter Login
          </Link>
          <Link to="/talentos/employee" className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700">
            Employee Login
          </Link>
        </div>
      </section>
    );
  }

  if (principalQuery.isLoading) {
    return (
      <section className="rounded-[2rem] bg-white p-10 shadow-panel text-sm text-slate-600">
        Loading your dashboard...
      </section>
    );
  }

  if (principalQuery.data?.role === "recruiter") {
    return <Navigate to="/talentos/recruiter" replace />;
  }

  if (principalQuery.data?.role === "employee") {
    return <Navigate to="/talentos/employee" replace />;
  }

  return <Navigate to="/" replace />;
}
