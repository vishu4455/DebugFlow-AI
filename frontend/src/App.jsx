import { useState, useCallback } from "react";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./components/auth/LoginPage";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import InputPanel from "./components/InputPanel";
import AgentPipeline from "./components/AgentPipeline";
import MetadataPanel from "./components/MetadataPanel";
import ClassificationPanel from "./components/ClassificationPanel";
import DependencyPanel from "./components/DependencyPanel";
import FixPanel from "./components/FixPanel";
import AirflowPanel from "./components/airflow/AirflowPanel";
import { useStreamDebug } from "./hooks/useStreamDebug";
import { PIPELINE_PRESETS } from "./services/presets";

const VIEWS = [
  { id: "debug",   label: "🔬 Debugger",        desc: "Run agents" },
  { id: "airflow", label: "🌀 Airflow Logs",     desc: "Browse & fetch" },
];

export default function App() {
  const { token } = useAuth();
  const [view, setView] = useState("debug");
  const [selectedPreset, setSelectedPreset] = useState("etl_sales");
  const [form, setForm] = useState({
    pipeline_id:     PIPELINE_PRESETS.etl_sales.id,
    error_logs:      PIPELINE_PRESETS.etl_sales.logs,
    pipeline_config: PIPELINE_PRESETS.etl_sales.config,
    log_source:      PIPELINE_PRESETS.etl_sales.source,
  });
  const [sessionId, setSessionId] = useState(null);
  const [airflowNotice, setAirflowNotice] = useState(null);

  const {
    agentStates, agentTimings, agentData,
    streaming, done, error,
    startStream, reset,
  } = useStreamDebug();

  if (!token) return <LoginPage />;

  const handlePresetChange = useCallback((key) => {
    setSelectedPreset(key);
    const p = PIPELINE_PRESETS[key];
    setForm({ pipeline_id: p.id, error_logs: p.logs, pipeline_config: p.config, log_source: p.source });
  }, []);

  const handleFormChange = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (selectedPreset !== "custom") setSelectedPreset("custom");
  }, [selectedPreset]);

  const handleClear = useCallback(() => { reset(); setSessionId(null); setAirflowNotice(null); }, [reset]);

  const handleRun = useCallback(() => {
    if (!form.error_logs.trim() && form.log_source === "inline") return;
    const sid = `session_${Date.now()}`;
    setSessionId(sid);
    startStream({
      pipeline_id:     form.pipeline_id || "unknown_pipeline",
      error_logs:      form.error_logs,
      pipeline_config: form.pipeline_config,
      log_source:      form.log_source,
    });
  }, [form, startStream]);

  // Called by AirflowPanel when user clicks "Use in Debugger"
  const handleAirflowLogsReady = useCallback((dagId, logs) => {
    setForm(prev => ({
      ...prev,
      pipeline_id: dagId,
      error_logs:  logs,
      log_source:  "inline", // logs are now loaded inline
    }));
    setSelectedPreset("custom");
    setAirflowNotice(`Logs loaded from Airflow DAG "${dagId}" — switch to Debugger tab to run agents.`);
    // Auto-switch to debugger view
    setView("debug");
  }, []);

  const sidebarStatus = streaming ? "running" : done ? "success" : error ? "error" : "idle";
  const panelStatus = (key) => {
    const s = agentStates[key];
    if (s === "idle")    return "pending";
    if (s === "running") return "running";
    if (s === "error")   return "error";
    return "success";
  };

  return (
    <div className="flex h-screen bg-navy-900 overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="w-64 bg-navy-800 border-r border-border flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-border">
          <div className="text-[10px] text-slate-600 uppercase tracking-widest mb-1 font-mono">Agentic AI</div>
          <div className="text-base font-bold text-accent-blue font-mono tracking-tight">Pipeline Debugger</div>
        </div>

        {/* View nav */}
        <div className="px-3 py-4 border-b border-border">
          <div className="text-[10px] text-slate-700 uppercase tracking-widest px-2 mb-3 font-mono">Views</div>
          {VIEWS.map(v => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 border transition-all duration-150 ${
                view === v.id
                  ? "bg-navy-600 border-border text-slate-200"
                  : "bg-transparent border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              <div>
                <div className="text-xs font-semibold leading-none mb-0.5">{v.label}</div>
                <div className="text-[10px] text-slate-600 font-mono">{v.desc}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Agent status (only meaningful in debug view) */}
        <Sidebar agentStates={agentStates} sidebarStatus={sidebarStatus} embedded />
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar
          selectedPreset={selectedPreset}
          onPresetChange={handlePresetChange}
          onClear={handleClear}
          onRun={handleRun}
          running={streaming}
          showRunButton={view === "debug"}
        />

        <main className="flex-1 overflow-auto p-5 space-y-5">
          {/* Airflow-loaded-logs notice */}
          {airflowNotice && (
            <div className="flex items-center gap-3 bg-green-950 border border-green-900/40 text-green-400 text-xs font-mono px-4 py-3 rounded-lg">
              <span>✓</span>
              <span className="flex-1">{airflowNotice}</span>
              <button onClick={() => setAirflowNotice(null)} className="opacity-50 hover:opacity-100">✕</button>
            </div>
          )}

          {error && (
            <div className="bg-red-950 border border-red-900/50 text-accent-red text-xs font-mono px-4 py-3 rounded-lg flex items-center gap-2">
              <span className="text-base">⚠</span> {error}
            </div>
          )}

          {/* ── DEBUGGER VIEW ── */}
          {view === "debug" && (
            <>
              <InputPanel form={form} onChange={handleFormChange} />
              <AgentPipeline agentStates={agentStates} agentTimings={agentTimings} />
              <div className="grid grid-cols-2 gap-4">
                <MetadataPanel status={panelStatus("metadata")} data={agentData.metadata} />
                <ClassificationPanel
                  status={panelStatus("classification")} data={agentData.classification}
                  pipelineId={form.pipeline_id} sessionId={sessionId}
                />
                <DependencyPanel status={panelStatus("dependency")} data={agentData.dependency} />
                <FixPanel
                  status={panelStatus("fix")} data={agentData.fix}
                  pipelineId={form.pipeline_id} sessionId={sessionId}
                />
              </div>
              {done && (
                <div className="text-center text-[11px] text-slate-600 font-mono pb-2 animate-fade-in">
                  ✓ All agents complete
                  {Object.values(agentTimings).length > 0 && (
                    <> · Total: {(Object.values(agentTimings).reduce((a, b) => a + b, 0) / 1000).toFixed(1)}s</>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── AIRFLOW VIEW ── */}
          {view === "airflow" && (
            <>
              <div className="card">
                <div className="card-header">
                  <div className="card-title">🌀 Airflow Log Fetcher</div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Browse DAGs → find failures → load logs into debugger
                  </span>
                </div>
                <div className="p-5">
                  <AirflowPanel onLogsReady={handleAirflowLogsReady} />
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
