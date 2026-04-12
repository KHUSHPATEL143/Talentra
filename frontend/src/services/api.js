import axios from "axios";

const LOCAL_STORAGE_API_KEY = "garuda_api_key";
const LOCAL_STORAGE_AUTH_TOKEN = "garuda_auth_token";
const PARSE_RESULT_STORAGE_PREFIX = "garuda_parse_result:";

export function getClientApiKey() {
  if (typeof window === "undefined") {
    return process.env.REACT_APP_API_KEY || "";
  }
  return window.localStorage.getItem(LOCAL_STORAGE_API_KEY) || process.env.REACT_APP_API_KEY || "";
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

export function getAuthToken() {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(LOCAL_STORAGE_AUTH_TOKEN) || "";
}

export function setAuthToken(value) {
  if (typeof window === "undefined") {
    return;
  }
  if (value) {
    window.localStorage.setItem(LOCAL_STORAGE_AUTH_TOKEN, value);
  } else {
    window.localStorage.removeItem(LOCAL_STORAGE_AUTH_TOKEN);
  }
}

export function clearAuthToken() {
  setAuthToken("");
}

export function cacheParseResult(candidateId, payload) {
  if (typeof window === "undefined" || !candidateId || !payload) {
    return;
  }
  window.sessionStorage.setItem(`${PARSE_RESULT_STORAGE_PREFIX}${candidateId}`, JSON.stringify(payload));
}

export function getCachedParseResult(candidateId) {
  if (typeof window === "undefined" || !candidateId) {
    return null;
  }
  const rawValue = window.sessionStorage.getItem(`${PARSE_RESULT_STORAGE_PREFIX}${candidateId}`);
  if (!rawValue) {
    return null;
  }
  try {
    return JSON.parse(rawValue);
  } catch {
    return null;
  }
}

export function getApiErrorDetails(error) {
  const fallback = {
    code: "request_failed",
    message: "Request failed. Please try again.",
    traceId: "",
    partialResult: null
  };

  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const payload = error.response?.data;
  if (payload?.message) {
    return {
      code: payload.error || fallback.code,
      message: payload.message,
      traceId: payload.trace_id || "",
      partialResult: payload.partial_result || null
    };
  }

  return {
    ...fallback,
    message: error.message || fallback.message
  };
}

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1"
});

api.interceptors.request.use((config) => {
  const nextConfig = { ...config };
  nextConfig.headers = nextConfig.headers || {};
  const apiKey = getClientApiKey();
  if (apiKey) {
    nextConfig.headers["X-API-Key"] = apiKey;
  }
  const authToken = getAuthToken();
  if (authToken) {
    nextConfig.headers.Authorization = `Bearer ${authToken}`;
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

export async function registerRecruiter(payload) {
  const response = await api.post("/auth/register-recruiter", payload);
  return response.data;
}

export async function registerEmployee(payload) {
  const response = await api.post("/auth/register-employee", payload);
  return response.data;
}

export async function login(payload) {
  const response = await api.post("/auth/login", payload);
  return response.data;
}

export async function getCurrentPrincipal() {
  const response = await api.get("/auth/me");
  return response.data;
}

export async function getEmployeeProfile() {
  const response = await api.get("/employee/profile");
  return response.data;
}

export async function updateEmployeeProfile(payload) {
  const response = await api.put("/employee/profile", payload);
  return response.data;
}

export async function verifyEmployeeProfile() {
  const response = await api.post("/employee/verify");
  return response.data;
}

export async function listEmployeeJobs() {
  const response = await api.get("/employee/jobs");
  return response.data;
}

export async function syncEmployeeSocialProfiles() {
  const response = await api.post("/employee/social-sync");
  return response.data;
}

export async function getEmployeeCareerCoach() {
  const response = await api.get("/employee/career-coach");
  return response.data;
}

export async function createRecruiterJob(payload) {
  const response = await api.post("/jobs", payload);
  return response.data;
}

export async function listRecruiterJobs() {
  const response = await api.get("/jobs");
  return response.data;
}

export async function getRecruiterJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

export async function runRecruiterMatching(jobId) {
  const response = await api.post(`/jobs/${jobId}/run-matching`);
  return response.data;
}

export async function getRecruiterCandidates(jobId, params = {}) {
  const response = await api.get(`/jobs/${jobId}/candidates`, { params });
  return response.data;
}

export async function updateRecruiterCandidateStage(jobId, candidateId, payload) {
  const response = await api.post(`/jobs/${jobId}/candidates/${candidateId}/stage`, payload);
  return response.data;
}

export default api;
