import PropTypes from "prop-types";
import { useMemo } from "react";
import { useDropzone } from "react-dropzone";

const formatConfig = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/plain": [".txt"]
};

export default function FileDropzone({ onFileAccepted, multiple = false }) {
  const {
    getRootProps,
    getInputProps,
    acceptedFiles,
    fileRejections
  } = useDropzone({
    accept: formatConfig,
    maxSize: 10 * 1024 * 1024,
    multiple,
    onDropAccepted: onFileAccepted
  });

  const rejectionMessage = useMemo(() => {
    if (!fileRejections.length) return "";
    return fileRejections[0].errors[0]?.message || "File rejected.";
  }, [fileRejections]);

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className="rounded-[2rem] border-2 border-dashed border-slate-300 bg-white/80 p-10 text-center shadow-panel transition hover:border-sky-400 hover:bg-sky-50/50"
      >
        <input {...getInputProps()} />
        <p className="font-display text-2xl font-bold text-slate-900">Drop resumes here</p>
        <p className="mt-2 text-sm text-slate-500">PDF, DOCX, and TXT up to 10MB each</p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {["PDF", "DOCX", "TXT"].map((label) => (
            <span key={label} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
              {label}
            </span>
          ))}
        </div>
      </div>
      {acceptedFiles.length ? (
        <div className="rounded-3xl bg-white p-4 shadow-panel">
          <p className="text-sm font-semibold text-slate-700">Selected files</p>
          <div className="mt-3 space-y-2">
            {acceptedFiles.map((file) => (
              <div key={file.path} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-sm">
                <span className="font-medium text-slate-800">{file.name}</span>
                <span className="text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {rejectionMessage ? <p className="text-sm font-medium text-red-600">{rejectionMessage}</p> : null}
    </div>
  );
}

FileDropzone.propTypes = {
  onFileAccepted: PropTypes.func.isRequired,
  multiple: PropTypes.bool
};
