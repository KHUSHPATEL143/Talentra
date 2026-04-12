import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, Navigate } from "react-router-dom";
import {
  getAuthToken,
  getCurrentPrincipal,
  login,
  registerEmployee,
  registerRecruiter,
  setAuthToken
} from "../services/api";

const roles = [
  {
    id: "recruiter",
    eyebrow: "Recruiter",
    title: "Hire with a focused command center",
    description: "Create roles, run ranking, and manage a live hiring pipeline."
  },
  {
    id: "employee",
    eyebrow: "Employee",
    title: "Build a verified professional profile",
    description: "Turn your projects and skills into a stronger job-facing profile."
  }
];

export default function LoginHub() {
  const [selectedRole, setSelectedRole] = useState("recruiter");
  const hasToken = Boolean(getAuthToken());
  const principalQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasToken
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      window.location.href = data.role === "recruiter" ? "/talentos/recruiter" : "/talentos/employee";
    }
  });

  const registerMutation = useMutation({
    mutationFn: async (payload) => {
      if (selectedRole === "recruiter") {
        await registerRecruiter(payload);
      } else {
        await registerEmployee(payload);
      }
      return payload;
    },
    onSuccess: (payload) => {
      loginMutation.mutate({
        email: payload.email,
        password: payload.password
      });
    }
  });

  const roleMeta = useMemo(
    () => roles.find((role) => role.id === selectedRole) || roles[0],
    [selectedRole]
  );

  if (principalQuery.data?.role === "recruiter") {
    return <Navigate to="/talentos/recruiter" replace />;
  }

  if (principalQuery.data?.role === "employee") {
    return <Navigate to="/talentos/employee" replace />;
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(241,245,249,0.9),_rgba(248,250,252,1)),linear-gradient(180deg,_#fbfbf7_0%,_#f3f4ef_100%)] px-6 py-10">
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-[2.5rem] border border-stone-200/80 bg-white/85 p-10 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.38em] text-stone-500">TalentOS Access</p>
            <h1 className="mt-4 max-w-3xl font-display text-5xl font-bold leading-[1.05] text-slate-950">
              One calm entry point for both sides of hiring.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600">
              Choose a role first. We only reveal the workflows, data, and actions that belong to that side of the platform.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => setSelectedRole(role.id)}
                  className={`rounded-[2rem] border px-6 py-6 text-left transition ${
                    selectedRole === role.id
                      ? "border-slate-900 bg-slate-950 text-white shadow-[0_18px_40px_rgba(15,23,42,0.16)]"
                      : "border-stone-200 bg-stone-50/80 text-slate-800 hover:border-stone-300 hover:bg-white"
                  }`}
                >
                  <p className={`text-xs font-semibold uppercase tracking-[0.28em] ${selectedRole === role.id ? "text-stone-300" : "text-stone-500"}`}>
                    {role.eyebrow}
                  </p>
                  <h2 className="mt-3 text-2xl font-semibold">{role.title}</h2>
                  <p className={`mt-3 text-sm leading-7 ${selectedRole === role.id ? "text-slate-200" : "text-slate-600"}`}>
                    {role.description}
                  </p>
                </button>
              ))}
            </div>
            <div className="mt-10 rounded-[2rem] bg-stone-100/80 p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">Selected Role</p>
              <h3 className="mt-3 text-2xl font-semibold text-slate-900">{roleMeta.title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">{roleMeta.description}</p>
            </div>
          </section>

          <section className="rounded-[2.5rem] border border-stone-200/80 bg-white/90 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-stone-500">{roleMeta.eyebrow} Access</p>
                <h2 className="mt-2 font-display text-3xl font-bold text-slate-950">Continue as {roleMeta.eyebrow}</h2>
              </div>
              <Link to="/" className="rounded-full border border-stone-200 px-4 py-2 text-sm font-semibold text-slate-700">
                Product Page
              </Link>
            </div>

            <div className="mt-8 grid gap-5">
              <RoleForm
                title={selectedRole === "recruiter" ? "Create Recruiter Account" : "Create Employee Account"}
                fields={
                  selectedRole === "recruiter"
                    ? [
                        { name: "name", label: "Name" },
                        { name: "email", label: "Email", type: "email" },
                        { name: "password", label: "Password", type: "password" },
                        { name: "company_name", label: "Company" }
                      ]
                    : [
                        { name: "name", label: "Name" },
                        { name: "email", label: "Email", type: "email" },
                        { name: "password", label: "Password", type: "password" },
                        { name: "location", label: "Location" }
                      ]
                }
                extraCheckbox={selectedRole === "employee" ? { name: "open_to_relocation", label: "Open to relocation" } : null}
                buttonLabel={registerMutation.isPending ? "Creating..." : `Create ${roleMeta.eyebrow} Account`}
                error={registerMutation.error?.response?.data?.message || ""}
                onSubmit={(payload) => registerMutation.mutate(payload)}
              />

              <RoleForm
                title={`Login as ${roleMeta.eyebrow}`}
                fields={[
                  { name: "email", label: "Email", type: "email" },
                  { name: "password", label: "Password", type: "password" }
                ]}
                buttonLabel={loginMutation.isPending ? "Signing in..." : `Login as ${roleMeta.eyebrow}`}
                error={loginMutation.error?.response?.data?.message || ""}
                onSubmit={(payload) => loginMutation.mutate(payload)}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function RoleForm({ title, fields, extraCheckbox, buttonLabel, error, onSubmit }) {
  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    if (extraCheckbox) {
      payload[extraCheckbox.name] = formData.get(extraCheckbox.name) === "on";
    }
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-[2rem] border border-stone-200/80 bg-stone-50/70 p-6">
      <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
      <div className="mt-5 space-y-3">
        {fields.map((field) => (
          <label key={field.name} className="block">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">{field.label}</span>
            <input
              name={field.name}
              type={field.type || "text"}
              required
              className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm outline-none focus:border-slate-400"
            />
          </label>
        ))}
        {extraCheckbox ? (
          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" name={extraCheckbox.name} />
            {extraCheckbox.label}
          </label>
        ) : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
          {buttonLabel}
        </button>
      </div>
    </form>
  );
}
