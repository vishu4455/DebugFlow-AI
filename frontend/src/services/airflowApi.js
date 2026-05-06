// src/services/airflowApi.js
// All frontend calls to the Airflow integration endpoints

import api from "./api";

export const getAirflowStatus   = ()           => api.get("/airflow/status");
export const getAirflowDags     = ()           => api.get("/airflow/dags");
export const getDagRuns         = (dagId, params) => api.get(`/airflow/dags/${dagId}/runs`, { params });
export const getTaskInstances   = (dagId, runId) => api.get(`/airflow/dags/${dagId}/runs/${runId}/tasks`);
export const getTaskLogs        = (dagId, runId, taskId, tryNum = 1) =>
  api.get(`/airflow/dags/${dagId}/runs/${runId}/tasks/${taskId}/logs`, { params: { try_number: tryNum } });
export const fetchLogsAuto      = (payload)    => api.post("/airflow/fetch-logs", payload);
