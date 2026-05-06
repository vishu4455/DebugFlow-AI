import { useState, useEffect, useCallback } from "react";
import {
  getAirflowStatus, getAirflowDags, getDagRuns,
  getTaskInstances, getTaskLogs, fetchLogsAuto,
} from "../../services/airflowApi";

// ─── tiny helpers ──────────────────────────────────────────────────────────
const STATE_COLOR = {
  success: "text-green-400 bg-green-950 border-green-900/40",
  failed:  "text-red-400 bg-red-950 border-red-900/40",
  running: "text-amber-400 bg-amber-950 border-amber-900/40",
  queued:  "text-blue-400 bg-blue-950 border-blue-900/40",
  skipped: "text-slate-500 bg-slate-900 border-slate-800",
  upstream_failed: "text-orange-400 bg-orange-950 border-orange-900/40",
};
const stateBadge = (s) => (
  <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border font-mono ${STATE_COLOR[s] || "text-slate-500 bg-slate-900 border-slate-800"}`}>
    {s || "—"}
  </span>
);

function Spinner({ size = 14 }) {
  return (
    <div
      style={{ width: size, height: size }}
      className="border-2 border-slate-700 border-t-accent-blue rounded-full animate-spin-slow flex-shrink-0"
    />
  );
}

function Section({ title, icon, children, action }) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">{icon} {title}</div>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

// ─── Connection Status Banner ──────────────────────────────────────────────
function ConnectionBanner({ status, onRefresh }) {
  if (!status) return null;
  const ok = status.ok;
  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-lg border text-xs font-mono ${
      ok ? "bg-green-950 border-green-900/40 text-green-400"
         : "bg-red-950 border-red-900/40 text-red-400"
    }`}>
      <span className="text-base mt-0.5">{ok ? "✓" : "✗"}</span>
      <div className="flex-1">
        <div className="font-semibold mb-0.5">{ok ? "Airflow Connected" : "Airflow Unreachable"}</div>
        <div className="text-[11px] opacity-80">{status.message}</div>
        {ok && (
          <div className="text-[10px] opacity-60 mt-0.5">
            Version: {status.version} · {status.base_url}
          </div>
        )}
        {!ok && status.diagnosis && (
          <pre className="mt-2 text-[10px] whitespace-pre-wrap opacity-70">{status.diagnosis}</pre>
        )}
      </div>
      <button onClick={onRefresh} className="text-[10px] opacity-60 hover:opacity-100 border border-current px-2 py-1 rounded">
        ↺ Retry
      </button>
    </div>
  );
}

// ─── DAG List ──────────────────────────────────────────────────────────────
function DagList({ dags, loading, selected, onSelect }) {
  const [filter, setFilter] = useState("");
  const filtered = dags.filter(d =>
    d.dag_id.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-2">
      <input
        className="field-input"
        placeholder="Filter DAGs…"
        value={filter}
        onChange={e => setFilter(e.target.value)}
      />
      {loading && <div className="flex items-center gap-2 text-slate-600 text-xs font-mono py-2"><Spinner />Loading DAGs…</div>}
      {!loading && filtered.length === 0 && (
        <div className="text-slate-600 text-xs font-mono py-4 text-center">No DAGs found</div>
      )}
      <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
        {filtered.map(dag => (
          <button
            key={dag.dag_id}
            onClick={() => onSelect(dag.dag_id)}
            className={`w-full text-left px-3 py-2.5 rounded-lg border text-xs font-mono transition-all duration-150 ${
              selected === dag.dag_id
                ? "bg-navy-500 border-accent-blue text-accent-blue"
                : "bg-navy-800 border-border text-slate-400 hover:border-slate-500 hover:text-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold truncate">{dag.dag_id}</span>
              <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                {dag.is_paused && (
                  <span className="text-[9px] text-amber-500 border border-amber-900/40 bg-amber-950 px-1.5 py-0.5 rounded">paused</span>
                )}
                {dag.tags?.slice(0,2).map(t => (
                  <span key={t} className="text-[9px] text-slate-600 border border-border px-1.5 py-0.5 rounded">{t}</span>
                ))}
              </div>
            </div>
            {dag.description && (
              <div className="text-[10px] text-slate-600 mt-0.5 truncate">{dag.description}</div>
            )}
            {dag.schedule && (
              <div className="text-[10px] text-slate-700 mt-0.5">⏱ {dag.schedule}</div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Run List ──────────────────────────────────────────────────────────────
function RunList({ runs, loading, selected, onSelect }) {
  if (loading) return <div className="flex items-center gap-2 text-slate-600 text-xs font-mono py-2"><Spinner />Loading runs…</div>;
  if (!runs.length) return <div className="text-slate-600 text-xs font-mono py-4 text-center">No runs found</div>;

  return (
    <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
      {runs.map(run => (
        <button
          key={run.dag_run_id}
          onClick={() => onSelect(run)}
          className={`w-full text-left px-3 py-2.5 rounded-lg border text-xs font-mono transition-all duration-150 ${
            selected?.dag_run_id === run.dag_run_id
              ? "bg-navy-500 border-accent-blue"
              : "bg-navy-800 border-border text-slate-400 hover:border-slate-500"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="truncate text-[11px]">{run.dag_run_id}</span>
            {stateBadge(run.state)}
          </div>
          <div className="text-[10px] text-slate-600 mt-0.5 flex gap-3">
            <span>{run.execution_date?.slice(0, 16).replace("T", " ")}</span>
            {run.duration_sec && <span>{run.duration_sec}s</span>}
          </div>
        </button>
      ))}
    </div>
  );
}

// ─── Task List ─────────────────────────────────────────────────────────────
function TaskList({ tasks, loading, selected, onSelect }) {
  if (loading) return <div className="flex items-center gap-2 text-slate-600 text-xs font-mono py-2"><Spinner />Loading tasks…</div>;
  if (!tasks.length) return <div className="text-slate-600 text-xs font-mono py-4 text-center">No tasks found</div>;

  return (
    <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
      {tasks.map(task => (
        <button
          key={task.task_id}
          onClick={() => onSelect(task)}
          className={`w-full text-left px-3 py-2.5 rounded-lg border text-xs font-mono transition-all ${
            selected?.task_id === task.task_id
              ? "bg-navy-500 border-accent-blue"
              : "bg-navy-800 border-border text-slate-400 hover:border-slate-500"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold truncate">{task.task_id}</span>
            {stateBadge(task.state)}
          </div>
          <div className="text-[10px] text-slate-600 mt-0.5 flex gap-3">
            <span>{task.operator}</span>
            <span>Try #{task.try_number}/{task.max_tries + 1}</span>
            {task.duration && <span>{task.duration}s</span>}
          </div>
        </button>
      ))}
    </div>
  );
}

// ─── Log Viewer ────────────────────────────────────────────────────────────
function LogViewer({ logs, warnings, sourceUrl, loading, error, onUseInDebugger }) {
  const [search, setSearch] = useState("");

  const highlighted = search
    ? logs?.split("\n").filter(l => l.toLowerCase().includes(search.toLowerCase()))
    : logs?.split("\n");

  return (
    <div className="space-y-3">
      {warnings?.map((w, i) => (
        <div key={i} className="text-[11px] text-amber-400 bg-amber-950 border border-amber-900/40 px-3 py-2 rounded font-mono">
          ⚠ {w}
        </div>
      ))}

      {error && (
        <div className="bg-red-950 border border-red-900/40 rounded-lg p-4 space-y-2">
          <div className="text-accent-red text-xs font-semibold font-mono">✗ Log fetch failed</div>
          <pre className="text-red-300 text-[11px] whitespace-pre-wrap font-mono leading-relaxed">{error}</pre>
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-slate-600 text-xs font-mono py-4">
          <Spinner /> Fetching logs from Airflow…
        </div>
      )}

      {logs && !loading && (
        <>
          <div className="flex items-center gap-2">
            <input
              className="field-input flex-1 text-[11px]"
              placeholder="Search logs…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <span className="text-[10px] text-slate-500 font-mono flex-shrink-0">
                {highlighted?.length} lines
              </span>
            )}
            <button
              onClick={onUseInDebugger}
              className="btn btn-primary text-[10px] flex-shrink-0"
            >
              ↗ Use in Debugger
            </button>
          </div>

          {sourceUrl && (
            <div className="text-[10px] text-slate-600 font-mono">
              Source: <span className="text-accent-blue">{sourceUrl}</span>
            </div>
          )}

          <div className="bg-navy-900 border border-border rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-2 bg-navy-800 border-b border-border">
              <span className="text-[10px] text-slate-600 font-mono">
                {logs.split("\n").length} lines · {(logs.length / 1024).toFixed(1)} KB
              </span>
              <button
                onClick={() => navigator.clipboard?.writeText(logs)}
                className="text-[10px] text-slate-600 hover:text-slate-400 font-mono"
              >
                Copy
              </button>
            </div>
            <pre className="text-[11px] font-mono text-slate-300 p-4 overflow-auto max-h-80 leading-relaxed whitespace-pre-wrap">
              {(highlighted || []).map((line, i) => {
                const isError = /error|exception|failed|traceback/i.test(line);
                const isWarn  = /warn|warning/i.test(line);
                const isInfo  = /\[info\]|\sinfo\s/i.test(line);
                return (
                  <span
                    key={i}
                    className={
                      isError ? "text-red-400" :
                      isWarn  ? "text-amber-400" :
                      isInfo  ? "text-slate-500" :
                      "text-slate-300"
                    }
                  >
                    {line}{"\n"}
                  </span>
                );
              })}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Quick Fetch Section ───────────────────────────────────────────────────
function QuickFetch({ onLogsReady }) {
  const [dagId, setDagId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFetch = async () => {
    if (!dagId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await fetchLogsAuto({ dag_id: dagId.trim() });
      setResult(data);
      if (data.success && data.logs) onLogsReady?.(dagId.trim(), data.logs);
    } catch (err) {
      setResult({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="text-[11px] text-slate-500 font-mono">
        Enter a DAG ID — automatically finds the latest failed run and fetches its logs.
      </div>
      <div className="flex gap-2">
        <input
          className="field-input flex-1"
          placeholder="dag_id e.g. etl_sales_daily"
          value={dagId}
          onChange={e => setDagId(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleFetch()}
        />
        <button
          onClick={handleFetch}
          disabled={loading || !dagId.trim()}
          className="btn btn-primary flex-shrink-0 flex items-center gap-2"
        >
          {loading ? <><Spinner size={12} /> Fetching…</> : "Fetch Logs ↗"}
        </button>
      </div>
      {result && !result.success && (
        <div className="bg-red-950 border border-red-900/40 rounded-lg p-4 space-y-2">
          <div className="text-accent-red text-xs font-semibold font-mono">✗ Failed</div>
          <pre className="text-red-300 text-[11px] whitespace-pre-wrap font-mono">{result.error}</pre>
          {result.diagnosis && (
            <>
              <div className="text-[10px] text-slate-500 font-mono mt-2 font-semibold">How to fix:</div>
              <pre className="text-slate-400 text-[11px] whitespace-pre-wrap font-mono">{result.diagnosis}</pre>
            </>
          )}
        </div>
      )}
      {result?.success && (
        <div className="text-accent-green text-[11px] font-mono bg-green-950 border border-green-900/40 px-3 py-2 rounded flex items-center gap-2">
          ✓ Logs fetched ({(result.logs?.length / 1024).toFixed(1)} KB) — loaded into debugger
        </div>
      )}
    </div>
  );
}

// ─── Main AirflowPanel ────────────────────────────────────────────────────
export default function AirflowPanel({ onLogsReady }) {
  const [connStatus, setConnStatus] = useState(null);
  const [connLoading, setConnLoading] = useState(true);

  const [dags, setDags]               = useState([]);
  const [dagsLoading, setDagsLoading] = useState(false);

  const [selectedDag,  setSelectedDag]  = useState(null);
  const [runs,         setRuns]         = useState([]);
  const [runsLoading,  setRunsLoading]  = useState(false);

  const [selectedRun,   setSelectedRun]   = useState(null);
  const [tasks,         setTasks]         = useState([]);
  const [tasksLoading,  setTasksLoading]  = useState(false);

  const [selectedTask,  setSelectedTask]  = useState(null);
  const [logs,          setLogs]          = useState("");
  const [logWarnings,   setLogWarnings]   = useState([]);
  const [logSourceUrl,  setLogSourceUrl]  = useState("");
  const [logsLoading,   setLogsLoading]   = useState(false);
  const [logError,      setLogError]      = useState(null);

  const [activeTab, setActiveTab] = useState("quick"); // quick | browse

  // Test connection on mount
  const checkConnection = useCallback(async () => {
    setConnLoading(true);
    try {
      const status = await getAirflowStatus();
      setConnStatus(status);
      if (status.ok) loadDags();
    } catch (err) {
      setConnStatus({ ok: false, message: err.message });
    } finally {
      setConnLoading(false);
    }
  }, []);

  useEffect(() => { checkConnection(); }, [checkConnection]);

  const loadDags = useCallback(async () => {
    setDagsLoading(true);
    try {
      const data = await getAirflowDags();
      setDags(data.dags || []);
    } catch (err) {
      setDags([]);
    } finally {
      setDagsLoading(false);
    }
  }, []);

  const handleSelectDag = useCallback(async (dagId) => {
    setSelectedDag(dagId);
    setSelectedRun(null);
    setSelectedTask(null);
    setLogs(""); setLogError(null);
    setRunsLoading(true);
    try {
      const data = await getDagRuns(dagId, { limit: 15 });
      setRuns(data.runs || []);
    } catch (err) {
      setRuns([]);
    } finally {
      setRunsLoading(false);
    }
  }, []);

  const handleSelectRun = useCallback(async (run) => {
    setSelectedRun(run);
    setSelectedTask(null);
    setLogs(""); setLogError(null);
    setTasksLoading(true);
    try {
      const data = await getTaskInstances(selectedDag, run.dag_run_id);
      setTasks(data.tasks || []);
    } catch (err) {
      setTasks([]);
    } finally {
      setTasksLoading(false);
    }
  }, [selectedDag]);

  const handleSelectTask = useCallback(async (task) => {
    setSelectedTask(task);
    setLogs(""); setLogError(null); setLogWarnings([]);
    setLogsLoading(true);
    try {
      const data = await getTaskLogs(
        selectedDag,
        selectedRun.dag_run_id,
        task.task_id,
        task.try_number || 1,
      );
      setLogs(data.logs || "");
      setLogWarnings(data.warnings || []);
      setLogSourceUrl(data.source_url || "");
      if (data.logs) onLogsReady?.(selectedDag, data.logs);
    } catch (err) {
      setLogError(err.message);
    } finally {
      setLogsLoading(false);
    }
  }, [selectedDag, selectedRun, onLogsReady]);

  const TABS = [
    { id: "quick",  label: "⚡ Quick Fetch" },
    { id: "browse", label: "🗂 Browse DAGs" },
  ];

  return (
    <div className="space-y-4">
      {/* Connection status */}
      {connLoading ? (
        <div className="flex items-center gap-2 text-slate-600 text-xs font-mono px-4 py-3 bg-navy-800 border border-border rounded-lg">
          <Spinner /> Testing Airflow connection…
        </div>
      ) : (
        <ConnectionBanner status={connStatus} onRefresh={checkConnection} />
      )}

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-navy-800 border border-border rounded-lg w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-1.5 rounded text-xs font-mono font-semibold transition-all ${
              activeTab === tab.id
                ? "bg-navy-500 text-accent-blue border border-accent-blue/30"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Quick Fetch Tab ── */}
      {activeTab === "quick" && (
        <Section title="Auto-Fetch Latest Failure Logs" icon="⚡">
          <QuickFetch onLogsReady={onLogsReady} />
        </Section>
      )}

      {/* ── Browse Tab ── */}
      {activeTab === "browse" && (
        <div className="grid grid-cols-3 gap-4">
          {/* Column 1: DAGs */}
          <Section
            title="DAGs"
            icon="📋"
            action={
              <button onClick={loadDags} className="text-[10px] text-slate-600 hover:text-slate-400 font-mono">
                ↺ Refresh
              </button>
            }
          >
            <DagList
              dags={dags}
              loading={dagsLoading}
              selected={selectedDag}
              onSelect={handleSelectDag}
            />
          </Section>

          {/* Column 2: Runs */}
          <Section title={selectedDag ? `Runs — ${selectedDag}` : "Runs"} icon="▶">
            {!selectedDag ? (
              <div className="text-slate-600 text-xs font-mono py-4 text-center">← Select a DAG</div>
            ) : (
              <RunList
                runs={runs}
                loading={runsLoading}
                selected={selectedRun}
                onSelect={handleSelectRun}
              />
            )}
          </Section>

          {/* Column 3: Tasks */}
          <Section title={selectedRun ? "Tasks" : "Tasks"} icon="⚙">
            {!selectedRun ? (
              <div className="text-slate-600 text-xs font-mono py-4 text-center">← Select a run</div>
            ) : (
              <TaskList
                tasks={tasks}
                loading={tasksLoading}
                selected={selectedTask}
                onSelect={handleSelectTask}
              />
            )}
          </Section>
        </div>
      )}

      {/* Log viewer — shown in browse mode when a task is selected */}
      {activeTab === "browse" && selectedTask && (
        <Section
          title={`Logs — ${selectedTask.task_id} (try #${selectedTask.try_number})`}
          icon="📄"
        >
          <LogViewer
            logs={logs}
            warnings={logWarnings}
            sourceUrl={logSourceUrl}
            loading={logsLoading}
            error={logError}
            onUseInDebugger={() => onLogsReady?.(selectedDag, logs)}
          />
        </Section>
      )}
    </div>
  );
}
