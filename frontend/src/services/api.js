import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pfd_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("pfd_token");
      localStorage.removeItem("pfd_user");
      window.location.reload();
    }
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message || "Unknown error";
    return Promise.reject(new Error(msg));
  }
);

export const login            = (u, p) => api.post("/auth/login", { username: u, password: p });
export const getMe            = ()     => api.get("/auth/me");
export const debugFailure     = (p)    => api.post("/debug-failure", p);
export const getPipelineStatus= (id)   => api.get("/pipeline-status", { params: { pipeline_id: id } });
export const submitFeedback   = (p)    => api.post("/feedback", p);
export const getFeedbackMetrics= ()    => api.get("/feedback/metrics");
export const healthCheck      = ()     => api.get("/health");

export function openDebugStream(payload, { onEvent, onError, onDone }) {
  const token = localStorage.getItem("pfd_token");
  const ctrl  = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE_URL}/stream/debug`, {
        method: "POST",
        headers: {
          "Content-Type":  "application/json",
          "Authorization": token ? `Bearer ${token}` : "",
          "Accept":        "text/event-stream",
        },
        body:   JSON.stringify(payload),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        onError?.(new Error(`HTTP ${res.status}: ${text}`));
        return;
      }

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop();

        for (const block of lines) {
          const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          try {
            const event = JSON.parse(dataLine.slice(6));
            onEvent?.(event);
            if (event.step === "pipeline" && event.status === "complete") {
              onDone?.();
              return;
            }
          } catch { /* skip malformed */ }
        }
      }
      onDone?.();
    } catch (err) {
      if (err.name !== "AbortError") onError?.(err);
    }
  })();

  return { close: () => ctrl.abort() };
}

export default api;
