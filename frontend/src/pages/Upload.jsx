import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import BatchUploadTable from "../components/BatchUploadTable";
import FileDropzone from "../components/FileDropzone";
import { parseBatch, parseResume } from "../services/api";

export default function Upload() {
  const [singleFile, setSingleFile] = useState(null);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchJobId, setBatchJobId] = useState("");
  const navigate = useNavigate();

  const parseMutation = useMutation({
    mutationFn: () => parseResume(singleFile),
    onSuccess: (data) => navigate(`/candidates/${data.candidate_id}`)
  });

  const batchMutation = useMutation({
    mutationFn: () => parseBatch(batchFiles),
    onSuccess: (data) => setBatchJobId(data.job_id)
  });

  return (
    <div className="space-y-8">
      <section className="animate-rise rounded-[2rem] bg-slate-950 p-8 text-white shadow-panel">
        <p className="text-sm uppercase tracking-[0.35em] text-emerald-300">GARUDA</p>
        <h1 className="mt-3 max-w-3xl font-display text-4xl font-bold leading-tight md:text-5xl">
          Turn resumes into structured intelligence, normalized skills, and job-fit signals.
        </h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-300 md:text-base">
          Upload one resume for an instant candidate profile or push a full batch into the Redis-backed queue for concurrent processing.
        </p>
      </section>

      <section className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <h2 className="font-display text-2xl font-bold text-slate-900">Single Resume</h2>
            <p className="text-sm text-slate-500">Parse and normalize a single candidate synchronously.</p>
          </div>
          <FileDropzone multiple={false} onFileAccepted={(files) => setSingleFile(files[0])} />
          <button
            type="button"
            disabled={!singleFile || parseMutation.isPending}
            onClick={() => parseMutation.mutate()}
            className="rounded-full bg-sky-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {parseMutation.isPending ? "Parsing..." : "Upload Resume"}
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <h2 className="font-display text-2xl font-bold text-slate-900">Batch Intake</h2>
            <p className="text-sm text-slate-500">Queue up to 50 resumes and monitor progress in real time.</p>
          </div>
          <FileDropzone multiple onFileAccepted={(files) => setBatchFiles(files)} />
          <button
            type="button"
            disabled={!batchFiles.length || batchMutation.isPending}
            onClick={() => batchMutation.mutate()}
            className="rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {batchMutation.isPending ? "Queueing..." : "Queue Batch"}
          </button>
        </div>
      </section>

      <BatchUploadTable jobId={batchJobId} />
    </div>
  );
}
