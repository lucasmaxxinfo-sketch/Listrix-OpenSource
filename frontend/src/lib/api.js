import axios from "axios";

// REACT_APP_BACKEND_URL should point at the FastAPI backend. Fall back to the
// local dev backend when it is unset or still a "<SET_YOUR_VALUE_HERE>" placeholder
// so the app boots without a wall of failed requests.
const rawUrl = (process.env.REACT_APP_BACKEND_URL || "").trim();
const BACKEND_URL =
  rawUrl && !rawUrl.includes("<") && !rawUrl.includes("SET_YOUR")
    ? rawUrl.replace(/\/+$/, "")
    : "http://localhost:8000";
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, headers: { "Content-Type": "application/json" } });

// Attach the active workspace to every request (multi-tenant isolation) and the
// Bearer token when a user is signed in (auth-ready; no-op without a token).
api.interceptors.request.use((config) => {
  const wid = localStorage.getItem("listrix_workspace_id");
  if (wid) config.headers["X-Workspace-Id"] = wid;
  const token = localStorage.getItem("listrix_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ai status (probe is cached server-side ~30s)
export const getAIStatus = () => api.get("/ai/status").then((r) => r.data);

// auth
export const login = (d) => api.post("/auth/login", d).then((r) => r.data);
export const register = (d) => api.post("/auth/register", d).then((r) => r.data);
export const getMe = () => api.get("/auth/me").then((r) => r.data);

// workspaces
export const getWorkspaces = () => api.get("/workspaces").then((r) => r.data);
export const createWorkspace = (d) => api.post("/workspaces", d).then((r) => r.data);
export const updateWorkspace = (id, d) => api.put(`/workspaces/${id}`, d).then((r) => r.data);

// items & listings
export const createItem = (d) => api.post("/items", d).then((r) => r.data);
export const getItems = () => api.get("/items").then((r) => r.data);
export const getItem = (id) => api.get(`/items/${id}`).then((r) => r.data);
export const generateListing = (d) => api.post("/ai/generate", d).then((r) => r.data);
export const getListings = () => api.get("/listings").then((r) => r.data);
export const getEvents = () => api.get("/events").then((r) => r.data);
export const getFinancials = () => api.get("/financials").then((r) => r.data);
export const markItemSold = (id, d) => api.post(`/items/${id}/mark-sold`, d).then((r) => r.data);
export const markItemUnsold = (id) => api.post(`/items/${id}/mark-unsold`).then((r) => r.data);
export const setItemStage = (id, stage) => api.post(`/items/${id}/stage`, { stage }).then((r) => r.data);
export const uploadItemImage = (id, data) => api.post(`/items/${id}/image`, { data }).then((r) => r.data);

// images (object storage): items store an image_id; resolve to the served endpoint
export const imageSrc = (item, thumb = false) => {
  if (!item) return null;
  if (item.image_id) return `${API}/images/${item.image_id}${thumb ? "?thumb=1" : ""}`;
  return item.image || null;
};

// jobs
export const getJob = (id) => api.get(`/jobs/${id}`).then((r) => r.data);
export async function runAnalysisJob() {
  const { job_id, total, analyzed } = await api.post("/ai/analyze-all").then((r) => r.data);
  if (!job_id) return { analyzed: analyzed || 0 };
  for (let i = 0; i < 100; i += 1) {
    await new Promise((r) => setTimeout(r, 400));
    const j = await getJob(job_id);
    if (j.status === "done") return { analyzed: j.results, job: j };
    if (j.status === "failed") throw new Error(j.error || "Analysis job failed");
  }
  throw new Error("Analysis timed out");
}

// notifications
export const getNotifications = (unread) => api.get("/notifications", { params: unread ? { unread: 1 } : {} }).then((r) => r.data);
export const markAllNotificationsRead = () => api.post("/notifications/read").then((r) => r.data);

// search
export const searchAll = (q) => api.get("/search", { params: { q } }).then((r) => r.data);

// analytics
export const getAnalytics = () => api.get("/analytics").then((r) => r.data);

// inbox replies / read
export const draftReply = (id, text) => api.post(`/inbox/${id}/reply`, { text }).then((r) => r.data);
export const markInboxRead = (id) => api.post(`/inbox/${id}/read`).then((r) => r.data);

// workspace import + members
export const importCsv = (csv) => api.post("/workspaces/import", { csv }).then((r) => r.data);
export const getMembers = (wid) => api.get(`/workspaces/${wid}/members`).then((r) => r.data);
export const inviteMember = (wid, d) => api.post(`/workspaces/${wid}/members`, d).then((r) => r.data);
export const removeMember = (wid, memberId) => api.delete(`/workspaces/${wid}/members/${memberId}`).then((r) => r.data);
export const logClientEvent = (d) => api.post("/client-events", d).then((r) => r.data).catch(() => null);

// vision
export const visionAnalyze = (d) => api.post("/ai/vision/analyze", d).then((r) => r.data);

// marketing agent / action queue
export const analyzeItem = (id) => api.post(`/ai/analyze/${id}`).then((r) => r.data);
export const analyzeAll = () => api.post("/ai/analyze-all").then((r) => r.data);
export const getPerformance = () => api.get("/performance").then((r) => r.data);
export const getSuggestions = (status) => api.get("/suggestions", { params: status ? { status } : {} }).then((r) => r.data);
export const getItemSuggestions = (itemId) => api.get("/suggestions", { params: { item_id: itemId } }).then((r) => r.data);
export const applySuggestion = (id) => api.post(`/suggestions/${id}/apply`).then((r) => r.data);
export const dismissSuggestion = (id) => api.post(`/suggestions/${id}/dismiss`).then((r) => r.data);
export const editSuggestion = (id, body) => api.post(`/suggestions/${id}/edit`, body).then((r) => r.data);

// assistant / brief / intelligence
export const askAssistant = (d) => api.post("/ai/assistant", d).then((r) => r.data);
export const getBriefLatest = () => api.get("/brief/latest").then((r) => r.data);
export const generateBrief = () => api.post("/brief/generate").then((r) => r.data);
export const getPerformanceIntelligence = () => api.get("/performance-intelligence").then((r) => r.data);
export const getMarketSignals = () => api.get("/market/signals").then((r) => r.data);
export const getPriceHistory = (id) => api.get(`/price-history/${id}`).then((r) => r.data);
export const getCompetitors = (id) => api.get(`/competitors/${id}`).then((r) => r.data);
