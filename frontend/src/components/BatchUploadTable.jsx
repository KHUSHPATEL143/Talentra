import PropTypes from "prop-types";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getApiErrorDetails, getJobStatus } from "../services/api";

function StatusBadge({ status }) {
  const tone = {
    queued: "bg-slate-100 text-slate-700",
    processing: "bg-amber-100 text-amber-700",
    partial: "bg-amber-100 text-amber-700",
    done: "bg-emerald-100 text-emerald-700",
    failed: "bg-red-100 text-red-700"
  }[status] || "bg-slate-100 text-slate-700";

  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${tone}`}>{status}</span>;
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired
};

export default function BatchUploadTable({ jobId }) {
  const { data, error, isLoading } = useQuery({
    queryKey: ["job-status", jobId],
    queryFn: () => getJobStatus(jobId),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const nextStatus = query.state.data?.status;
      return nextStatus === "done" || nextStatus === "failed" ? false : 2000;
    }
  });

  if (!jobId) return null;

  const queryError = error ? getApiErrorDetails(error) : null;
  const completed = data?.completed_count || 0;
  const total = data?.total_count || 0;
  const progress = total ? Math.round((completed / total) * 100) : 0;
  const results = data?.results || [];
  const doneCount = results.filter((item) => item.status === "done").length;
  const partialCount = results.filter((item) => item.status === "partial").length;
  const failedCount = results.filter((item) => item.status === "failed").length;

  return (
    <div className="rounded-3xl bg-white p-6 shadow-panel">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Batch Status</h3>
          <p className="text-sm text-slate-500">Job ID: {jobId}</p>
        </div>
        <StatusBadge status={data?.status || "queued"} />
      </div>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <p className="mt-2 text-sm text-slate-600">{completed} of {total} files processed</p>
      <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold">
        <span className="rounded-full bg-emerald-100 px-3 py-2 text-emerald-700">{doneCount} complete</span>
        <span className="rounded-full bg-amber-100 px-3 py-2 text-amber-700">{partialCount} partial</span>
        <span className="rounded-full bg-red-100 px-3 py-2 text-red-700">{failedCount} failed</span>
      </div>
      {isLoading ? <p className="mt-4 text-sm text-slate-500">Loading live batch status...</p> : null}
      {queryError ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p className="font-semibold">Status polling failed</p>
          <p className="mt-1">{queryError.message}</p>
        </div>
      ) : null}
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="pb-3">Filename</th>
              <th className="pb-3">Candidate</th>
              <th className="pb-3">Status</th>
              <th className="pb-3">Details</th>
              <th className="pb-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {results.map((item) => (
              <tr key={item.job_id}>
                <td className="py-3">{item.file_name}</td>
                <td className="py-3">{item.candidate_id || "Pending"}</td>
                <td className="py-3"><StatusBadge status={item.status} /></td>
                <td className="py-3 text-slate-500">
                  {item.error ? item.error : item.partial ? "Parsed with fallback logic" : item.status === "done" ? "Ready for review" : "In progress"}
                </td>
                <td className="py-3">
                  {item.candidate_id ? (
                    <Link to={`/candidates/${item.candidate_id}`} className="font-semibold text-sky-600 hover:text-sky-700">
                      View candidate
                    </Link>
                  ) : (
                    <span className="text-slate-400">Unavailable</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data?.errors?.length ? <p className="mt-4 text-sm text-red-600">Errors: {data.errors.join(", ")}</p> : null}
    </div>
  );
}

BatchUploadTable.propTypes = {
  jobId: PropTypes.string
};

BatchUploadTable.defaultProps = {
  jobId: ""
};
