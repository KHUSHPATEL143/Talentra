import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getAuthToken,
  getCurrentPrincipal,
  getEmployeeCareerCoach,
  getEmployeeProfile,
  listEmployeeJobs,
  login,
  registerEmployee,
  setAuthToken,
  syncEmployeeSocialProfiles,
  updateEmployeeProfile,
  verifyEmployeeProfile
} from "../../../services/api";

export default function EmployeeConsole() {
  const queryClient = useQueryClient();
  const hasToken = Boolean(getAuthToken());
  const meQuery = useQuery({
    queryKey: ["auth-me"],
    queryFn: getCurrentPrincipal,
    retry: false,
    enabled: hasToken
  });
  const profileQuery = useQuery({
    queryKey: ["employee-profile"],
    queryFn: getEmployeeProfile,
    retry: false,
    enabled: meQuery.data?.role === "employee"
  });
  const jobsQuery = useQuery({
    queryKey: ["employee-jobs"],
    queryFn: listEmployeeJobs,
    retry: false,
    enabled: meQuery.data?.role === "employee"
  });
  const coachQuery = useQuery({
    queryKey: ["employee-career-coach"],
    queryFn: getEmployeeCareerCoach,
    retry: false,
    enabled: meQuery.data?.role === "employee"
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      window.location.reload();
    }
  });

  const registerMutation = useMutation({
    mutationFn: registerEmployee,
    onSuccess: (_, variables) => {
      loginMutation.mutate({
        email: variables.email,
        password: variables.password
      });
    }
  });

  const saveProfileMutation = useMutation({
    mutationFn: updateEmployeeProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employee-profile"] });
      queryClient.invalidateQueries({ queryKey: ["employee-jobs"] });
    }
  });

  const verifyMutation = useMutation({
    mutationFn: verifyEmployeeProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employee-profile"] });
      queryClient.invalidateQueries({ queryKey: ["employee-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["employee-career-coach"] });
    }
  });

  const syncMutation = useMutation({
    mutationFn: syncEmployeeSocialProfiles,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employee-profile"] });
      queryClient.invalidateQueries({ queryKey: ["employee-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["employee-career-coach"] });
    }
  });

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-white p-8 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">TalentOS Employee</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-slate-900">Employee Dashboard</h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          Build your verified profile with manual GitHub, LinkedIn, and LeetCode evidence, then preview how posted roles fit you.
        </p>
      </section>

      {meQuery.data?.role === "employee" ? (
        <>
          <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <EmployeeProfileForm
              profile={profileQuery.data}
              buttonLabel={saveProfileMutation.isPending ? "Saving..." : "Save Profile"}
              error={saveProfileMutation.error?.response?.data?.message || ""}
              onSubmit={(payload) => saveProfileMutation.mutate(payload)}
            />
            <section className="rounded-[2rem] bg-white p-8 shadow-panel">
              <p className="text-sm uppercase tracking-[0.3em] text-emerald-600">Verification</p>
              <h2 className="mt-3 font-display text-3xl font-bold text-slate-900">Signal strength for {meQuery.data.email}</h2>
              <p className="mt-4 text-sm text-slate-600">
                Save your manual evidence first, then run verification to turn claimed skills into recruiter-visible proof tiers.
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <StatCard label="Completeness" value={`${Math.round((profileQuery.data?.profile_completeness || 0) * 100)}%`} />
                <StatCard label="Verification" value={`${Math.round((profileQuery.data?.verification_score || 0) * 100)}%`} />
                <StatCard label="Claims" value={`${profileQuery.data?.claimed_skills?.length || 0}`} />
              </div>
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 disabled:opacity-60"
                >
                  {syncMutation.isPending ? "Syncing..." : "Sync Social Profiles"}
                </button>
                <button
                  type="button"
                  onClick={() => verifyMutation.mutate()}
                  disabled={verifyMutation.isPending}
                  className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
                >
                  {verifyMutation.isPending ? "Verifying..." : "Run Verification"}
                </button>
                <span className="rounded-full bg-slate-100 px-4 py-3 text-sm font-medium text-slate-600">
                  Status: {profileQuery.data?.scrape_status || "pending"}
                </span>
              </div>
              {syncMutation.error?.response?.data?.message || verifyMutation.error?.response?.data?.message ? (
                <p className="mt-4 text-sm text-rose-600">{syncMutation.error?.response?.data?.message || verifyMutation.error?.response?.data?.message}</p>
              ) : null}
              <div className="mt-6 space-y-3">
                {(profileQuery.data?.verified_skills || []).slice(0, 6).map((skill) => (
                  <div key={skill.canonical_name} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-slate-900">{skill.canonical_name}</strong>
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                        {skill.verification_tier}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {(skill.evidence || []).length ? `${skill.evidence.length} evidence signals attached.` : "No supporting evidence yet."}
                    </p>
                  </div>
                ))}
                {!profileQuery.data?.verified_skills?.length ? (
                  <p className="text-sm text-slate-500">No verified skills yet. Add claims and project evidence, then run verification.</p>
                ) : null}
              </div>
            </section>
          </section>

          <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <section className="rounded-[2rem] bg-white p-8 shadow-panel">
              <p className="text-sm uppercase tracking-[0.3em] text-stone-500">Career Coach</p>
              <h2 className="mt-3 font-display text-3xl font-bold text-slate-900">Skills to learn next</h2>
              <div className="mt-6 space-y-3">
                {(coachQuery.data?.recommended_skills || []).slice(0, 5).map((item) => (
                  <div key={item.skill} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-slate-900">{item.skill}</strong>
                      <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
                        {item.estimated_months} mo
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{item.reason}</p>
                  </div>
                ))}
                {!coachQuery.data?.recommended_skills?.length ? (
                  <p className="text-sm text-slate-500">Complete profile sync and verification to unlock stronger coaching recommendations.</p>
                ) : null}
              </div>
            </section>

            <section className="rounded-[2rem] bg-white p-8 shadow-panel">
              <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Score Trajectory</p>
              <h2 className="mt-3 font-display text-3xl font-bold text-slate-900">How one skill changes your score</h2>
              <div className="mt-6 space-y-3">
                {(coachQuery.data?.score_trajectories || []).slice(0, 4).map((item) => (
                  <div key={`${item.job_id}-${item.recommended_skill}`} className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-900">{item.job_title}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      Learn <strong>{item.recommended_skill}</strong>: {item.current_score} -> {item.projected_score}
                    </p>
                  </div>
                ))}
                {!coachQuery.data?.score_trajectories?.length ? (
                  <p className="text-sm text-slate-500">No score trajectory is available yet.</p>
                ) : null}
              </div>
            </section>
          </section>

          <section className="rounded-[2rem] bg-white p-8 shadow-panel">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Job Board</p>
            <h2 className="mt-3 font-display text-3xl font-bold text-slate-900">Public roles with your match preview</h2>
            <p className="mt-4 max-w-2xl text-sm text-slate-600">
              The board uses your current verified profile when available, and falls back to self-declared skills while you’re still filling things in.
            </p>
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {(jobsQuery.data?.items || []).map((job) => (
                <article key={job.id} className="rounded-[1.5rem] border border-slate-200 p-6">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{job.company}</p>
                  <h3 className="mt-2 text-2xl font-semibold text-slate-900">{job.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{job.location_label}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(job.required_skills || []).slice(0, 5).map((skill) => (
                      <span key={`${job.id}-${skill.skill}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                        {skill.skill}
                      </span>
                    ))}
                  </div>
                  {job.match_preview ? (
                    <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                      <p><strong className="text-slate-900">{job.match_preview.score}</strong> score · {job.match_preview.grade} grade</p>
                      <p className="mt-1">Location: {job.match_preview.location_status}</p>
                      <p className="mt-1">Missing: {(job.match_preview.missing_required || []).join(", ") || "None"}</p>
                      <p className="mt-2 text-slate-600">{job.match_preview.recommendation}</p>
                    </div>
                  ) : (
                    <p className="mt-5 text-sm text-slate-500">
                      Add location and enough matching skill signal to unlock a match preview for this role.
                    </p>
                  )}
                </article>
              ))}
              {!jobsQuery.data?.items?.length && !jobsQuery.isLoading ? (
                <p className="text-sm text-slate-500">No public jobs are available yet.</p>
              ) : null}
            </div>
          </section>
        </>
      ) : (
        <section className="grid gap-6 lg:grid-cols-2">
          <AuthForm
            title="Register Employee"
            fields={[
              { name: "name", label: "Name" },
              { name: "email", label: "Email", type: "email" },
              { name: "password", label: "Password", type: "password" },
              { name: "location", label: "Location" }
            ]}
            extraCheckbox={{ name: "open_to_relocation", label: "Open to relocation" }}
            buttonLabel={registerMutation.isPending ? "Creating..." : "Create Employee"}
            error={registerMutation.error?.response?.data?.message || ""}
            onSubmit={(payload) => registerMutation.mutate(payload)}
          />
          <AuthForm
            title="Login"
            fields={[
              { name: "email", label: "Email", type: "email" },
              { name: "password", label: "Password", type: "password" }
            ]}
            buttonLabel={loginMutation.isPending ? "Signing in..." : "Login"}
            error={loginMutation.error?.response?.data?.message || ""}
            onSubmit={(payload) => loginMutation.mutate(payload)}
          />
        </section>
      )}
    </div>
  );
}

function EmployeeProfileForm({ profile, buttonLabel, error, onSubmit }) {
  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      location: String(formData.get("location") || ""),
      open_to_relocation: formData.get("open_to_relocation") === "on",
      claimed_skills: String(formData.get("claimed_skills") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      github_username: String(formData.get("github_username") || ""),
      linkedin_url: String(formData.get("linkedin_url") || ""),
      leetcode_username: String(formData.get("leetcode_username") || ""),
      github_projects: String(formData.get("github_projects") || "")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [name, description = "", languages = ""] = line.split("|").map((item) => item.trim());
          return {
            name,
            description,
            url: "",
            languages: languages ? languages.split(",").map((item) => item.trim()).filter(Boolean) : [],
            topics: [],
            stars: 0,
            has_tests: false,
            has_ci: false
          };
        }),
      linkedin_manual: {
        current_role: String(formData.get("current_role") || ""),
        company: String(formData.get("current_company") || ""),
        location: String(formData.get("linkedin_location") || ""),
        experience_years: Number(formData.get("experience_years") || 0),
        skills_listed: String(formData.get("linkedin_skills") || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      },
      leetcode_manual: {
        easy: Number(formData.get("leetcode_easy") || 0),
        medium: Number(formData.get("leetcode_medium") || 0),
        hard: Number(formData.get("leetcode_hard") || 0),
        languages_used: String(formData.get("leetcode_languages") || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      }
    };
    onSubmit(payload);
  };

  const projectRows = (profile?.github_projects || [])
    .map((project) => [project.name, project.description, (project.languages || []).join(", ")].join(" | "))
    .join("\n");

  return (
    <form onSubmit={handleSubmit} className="rounded-[2rem] bg-white p-8 shadow-panel">
      <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Profile Builder</p>
      <h2 className="mt-3 font-display text-3xl font-bold text-slate-900">Manual proof that works for the demo</h2>
      <div className="mt-6 grid gap-4">
        <Field label="Location" name="location" defaultValue={profile?.location || ""} />
        <Field label="Claimed skills (comma separated)" name="claimed_skills" defaultValue={(profile?.claimed_skills || []).join(", ")} />
        <Field label="GitHub username" name="github_username" defaultValue={profile?.github_username || ""} />
        <Field label="LinkedIn URL" name="linkedin_url" defaultValue={profile?.linkedin_url || ""} />
        <Field label="LeetCode username" name="leetcode_username" defaultValue={profile?.leetcode_username || ""} />
        <TextArea
          label="Projects (one per line: name | description | lang1, lang2)"
          name="github_projects"
          defaultValue={projectRows}
          rows={5}
        />
        <Field label="Current role" name="current_role" defaultValue={profile?.linkedin_manual?.current_role || ""} />
        <Field label="Current company" name="current_company" defaultValue={profile?.linkedin_manual?.company || ""} />
        <Field label="LinkedIn location" name="linkedin_location" defaultValue={profile?.linkedin_manual?.location || ""} />
        <Field label="Experience years" name="experience_years" type="number" defaultValue={profile?.linkedin_manual?.experience_years || 0} />
        <Field label="LinkedIn skills (comma separated)" name="linkedin_skills" defaultValue={(profile?.linkedin_manual?.skills_listed || []).join(", ")} />
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="LeetCode easy" name="leetcode_easy" type="number" defaultValue={profile?.leetcode_manual?.easy || 0} />
          <Field label="LeetCode medium" name="leetcode_medium" type="number" defaultValue={profile?.leetcode_manual?.medium || 0} />
          <Field label="LeetCode hard" name="leetcode_hard" type="number" defaultValue={profile?.leetcode_manual?.hard || 0} />
        </div>
        <Field label="LeetCode languages" name="leetcode_languages" defaultValue={(profile?.leetcode_manual?.languages_used || []).join(", ")} />
        <label className="flex items-center gap-3 text-sm text-slate-700">
          <input type="checkbox" name="open_to_relocation" defaultChecked={profile?.open_to_relocation} />
          Open to relocation
        </label>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
          {buttonLabel}
        </button>
      </div>
    </form>
  );
}

function AuthForm({ title, fields, extraCheckbox, buttonLabel, error, onSubmit }) {
  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    if (extraCheckbox) {
      payload[extraCheckbox.name] = formData.get(extraCheckbox.name) === "on";
    }
    onSubmit(payload);
    event.currentTarget.reset();
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-[2rem] bg-white p-8 shadow-panel">
      <h2 className="font-display text-2xl font-bold text-slate-900">{title}</h2>
      <div className="mt-5 space-y-3">
        {fields.map((field) => (
          <label key={field.name} className="block">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{field.label}</span>
            <input
              name={field.name}
              type={field.type || "text"}
              required
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
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

function Field({ label, name, type = "text", defaultValue }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</span>
      <input
        name={name}
        type={type}
        defaultValue={defaultValue}
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
      />
    </label>
  );
}

function TextArea({ label, name, defaultValue, rows = 4 }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</span>
      <textarea
        name={name}
        defaultValue={defaultValue}
        rows={rows}
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-sky-400"
      />
    </label>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
