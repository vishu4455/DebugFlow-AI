import { useAuth } from "../context/AuthContext";
import { PIPELINE_PRESETS } from "../services/presets";

export default function Topbar({ selectedPreset, onPresetChange, onClear, onRun, running, showRunButton = true }) {
  const { user, logout } = useAuth();
  return (
    <div className="flex items-center gap-3 px-6 py-3.5 bg-navy-800 border-b border-border flex-shrink-0">
      <div className="text-sm font-semibold text-slate-400 flex-1 font-mono">
        Failure Debug Console
        <span className="ml-2 text-[10px] text-slate-600 font-normal">(SSE streaming)</span>
      </div>
      {showRunButton && (
        <>
          <select
            value={selectedPreset}
            onChange={(e) => onPresetChange(e.target.value)}
            className="bg-navy-700 border border-border text-accent-blue font-mono text-xs px-3 py-1.5 rounded focus:outline-none focus:border-accent-blue cursor-pointer"
          >
            {Object.entries(PIPELINE_PRESETS).map(([key, p]) => (
              <option key={key} value={key} className="bg-navy-800">{p.label}</option>
            ))}
          </select>
          <button className="btn btn-ghost" onClick={onClear} disabled={running}>Clear</button>
          <button className="btn btn-primary" onClick={onRun} disabled={running}>
            {running ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-blue-800 border-t-blue-400 rounded-full animate-spin-slow" />
                Streaming...
              </span>
            ) : "Run Agents ↗"}
          </button>
        </>
      )}
      {user && (
        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <div className="text-right hidden sm:block">
            <div className="text-[11px] text-slate-400 font-mono leading-none">{user.username}</div>
            <div className="text-[9px] text-slate-600 font-mono mt-0.5">{user.role}</div>
          </div>
          <button onClick={logout}
            className="text-[10px] text-slate-600 hover:text-accent-red transition-colors font-mono border border-border px-2 py-1 rounded hover:border-red-900"
            title="Sign out">
            ⎋ out
          </button>
        </div>
      )}
    </div>
  );
}
