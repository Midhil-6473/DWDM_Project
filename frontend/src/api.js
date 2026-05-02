import axios from "axios";

// In dev, empty baseURL + Vite proxy (vite.config.js) avoids wrong ports and mixed localhost/127.0.0.1.
// Set VITE_API_BASE_URL only if you want to bypass the proxy (full URL to FastAPI).
const explicit = import.meta.env.VITE_API_BASE_URL;
const API_BASE_URL =
  typeof explicit === "string" && explicit.trim().length > 0
    ? explicit.trim()
    : import.meta.env.DEV
      ? ""
      : "http://127.0.0.1:8005";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000 // 30s timeout for slow initial data loads
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message
    });
    return Promise.reject(error);
  }
);

export async function getFormMetadata() {
  const { data } = await api.get("/meta/form");
  return data;
}

export async function predictBoth(features) {
  const { data } = await api.post("/predict/both", { features });
  return data;
}

export async function getSummary(params) {
  const { data } = await api.get("/analytics/summary", { params });
  return data;
}

export async function getYieldDistribution(params) {
  const { data } = await api.get("/analytics/yield_distribution", { params });
  return data;
}

export async function getCategoryCounts(params) {
  const { data } = await api.get("/analytics/category_counts", { params });
  return data;
}

export async function getTopCrops(params) {
  const { data } = await api.get("/analytics/top_crops", { params });
  return data;
}

export async function getTopCropsByConditions(features, limit = 5) {
  const { data } = await api.post(`/analytics/top_crops_by_conditions?limit=${limit}`, { features });
  return data;
}

export async function getConditionDiagnostics(params) {
  const { data } = await api.get("/analytics/condition_diagnostics", { params });
  return data;
}
