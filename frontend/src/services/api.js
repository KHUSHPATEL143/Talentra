import axios from "axios";

const LOCAL_STORAGE_API_KEY = "garuda_api_key";

export function getClientApiKey() {
  if (typeof window === "undefined") {
    return import.meta.env.VITE_API_KEY || "";
  }
  return window.localStorage.getItem(LOCAL_STORAGE_API_KEY) || import.meta.env.VITE_API_KEY || "";
}

export function setClientApiKey(value) {
  if (typeof window === "undefined") {
    return;
  }
  if (value) {
    window.localStorage.setItem(LOCAL_STORAGE_API_KEY, value);
  } else {
    window.localStorage.removeItem(LOCAL_STORAGE_API_KEY);
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
});

api.interceptors.request.use((config) => {
  const nextConfig = { ...config };
  nextConfig.headers = nextConfig.headers || {};
  const apiKey = getClientApiKey();
  if (apiKey) {
    nextConfig.headers["X-API-Key"] = apiKey;
  }
  return nextConfig;
});

export async function parseResume(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

export async function parseBatch(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await api.post("/parse/batch", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

export async function getJobStatus(jobId) {
  const response = await api.get(`/jobs/${jobId}/status`);
  return response.data;
}

export async function getCandidate(candidateId) {
  const response = await api.get(`/candidates/${candidateId}`);
  return response.data;
}

export async function getCandidateSkills(candidateId) {
  const response = await api.get(`/candidates/${candidateId}/skills`);
  return response.data;
}

export async function matchCandidate(candidateId, jobDescription, weights, mode) {
  const response = await api.post("/match", {
    candidate_id: candidateId,
    job_description: jobDescription,
    weights,
    mode
  });
  return response.data;
}

export async function getTaxonomy(params = {}) {
  const response = await api.get("/skills/taxonomy", { params });
  return response.data;
}

export async function searchTaxonomy(q) {
  const response = await api.get("/skills/taxonomy/search", { params: { q } });
  return response.data;
}

export async function getTaxonomyStats() {
  const response = await api.get("/skills/taxonomy/stats");
  return response.data;
}

export async function registerWebhook(url, events) {
  const response = await api.post("/webhooks", { url, events });
  return response.data;
}

export default api;
