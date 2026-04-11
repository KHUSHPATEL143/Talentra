import { useMutation } from "@tanstack/react-query";
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FileUp, Files, Info } from "lucide-react";
import BatchUploadTable from "../components/BatchUploadTable";
import FileDropzone from "../components/FileDropzone";
import { parseBatch, parseResume } from "../services/api";

export default function Intake() {
  const [singleFile, setSingleFile] = useState(null);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchJobId, setBatchJobId] = useState("");
  const [activeTab, setActiveTab] = useState("single");
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
    <div className="pb-24 pt-10">
      <section id="intake" className="">
        <div className="mx-auto max-w-4xl px-0">
          <div className="text-center mb-12">
            <h1 className="font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">Intake Center</h1>
            <p className="mt-4 text-lg text-slate-600">
              Select your processing mode and upload resumes to begin extraction.
            </p>
          </div>
          
          <div className="rounded-[2.5rem] bg-white p-6 shadow-2xl shadow-slate-200/50 border border-slate-100">
            {/* Tab Navigation */}
            <div className="flex gap-2 rounded-2xl bg-slate-100 p-1.5 mb-8">
              <button
                onClick={() => setActiveTab("single")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold transition-all ${
                  activeTab === "single" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500 hover:text-slate-700 hover:bg-white/50"
                }`}
              >
                <FileUp size={18} />
                Single Resume
              </button>
              <button
                onClick={() => setActiveTab("batch")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold transition-all ${
                  activeTab === "batch" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500 hover:text-slate-700 hover:bg-white/50"
                }`}
              >
                <Files size={18} />
                Batch Intake
              </button>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.2 }}
                className="space-y-6 px-2 pb-2"
              >
                {activeTab === "single" ? (
                  <div className="space-y-6">
                    <div className="flex items-start gap-4 rounded-2xl bg-sky-50 p-5 text-sky-800 ring-1 ring-sky-200/50">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-600">
                        <Info size={20} />
                      </div>
                      <div className="space-y-1">
                        <p className="font-bold">Instant Analysis</p>
                        <p className="text-sm leading-relaxed opacity-90">
                          Best for individual review. The AI will parse this resume synchronously and redirect you to the candidate profile immediately.
                        </p>
                      </div>
                    </div>
                    <FileDropzone multiple={false} onFileAccepted={(files) => setSingleFile(files[0])} />
                    <button
                      type="button"
                      disabled={!singleFile || parseMutation.isPending}
                      onClick={() => parseMutation.mutate()}
                      className="w-full flex items-center justify-center gap-2 rounded-2xl bg-slate-950 py-4.5 text-lg font-bold text-white transition-all hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 active:scale-[0.98] shadow-xl shadow-slate-950/10"
                    >
                      {parseMutation.isPending ? (
                        <span className="flex items-center gap-3">
                          <svg className="h-6 w-6 animate-spin text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                          Synthesizing Data...
                        </span>
                      ) : "Process Candidate"}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="flex items-start gap-4 rounded-2xl bg-emerald-50 p-5 text-emerald-800 ring-1 ring-emerald-200/50">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
                        <Info size={20} />
                      </div>
                      <div className="space-y-1">
                        <p className="font-bold">Queue Processing</p>
                        <p className="text-sm leading-relaxed opacity-90">
                          Queue up to 50 resumes. Our Redis-backed worker pool will process them concurrently. You can track individual progress below.
                        </p>
                      </div>
                    </div>
                    <FileDropzone multiple onFileAccepted={(files) => setBatchFiles(files)} />
                    <button
                      type="button"
                      disabled={!batchFiles.length || batchMutation.isPending}
                      onClick={() => batchMutation.mutate()}
                      className="w-full flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-4.5 text-lg font-bold text-white transition-all hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 active:scale-[0.98] shadow-xl shadow-emerald-600/10"
                    >
                      {batchMutation.isPending ? (
                        <span className="flex items-center gap-3">
                          <svg className="h-6 w-6 animate-spin text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                          Initializing Worker Pool...
                        </span>
                      ) : `Batch Process ${batchFiles.length} Resumes`}
                    </button>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          <AnimatePresence>
            {batchJobId && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-16"
              >
                <div className="mb-6 flex items-center justify-between">
                  <h3 className="font-display text-2xl font-bold text-slate-900">Live Intake Queue</h3>
                  <div className="flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-600">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                    LIVE
                  </div>
                </div>
                <BatchUploadTable jobId={batchJobId} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>
    </div>
  );
}

