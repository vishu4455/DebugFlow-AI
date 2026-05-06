import { AGENT_META } from "../services/presets";

const DOT_COLORS = {
  idle:    "bg-slate-700",
  running: "bg-accent-amber animate-pulse",
  success: "bg-accent-green",
  error:   "bg-accent-red",
};

// embedded=true → rendered inside App's custom sidebar, skip the wrapper
export default function Sidebar({ agentStates, sidebarStatus, embedded = false }) {
  const inner = (
    <>
      <div className="flex-1 px-3 py-4">
        <div className="text-[10px] text-slate-700 uppercase tracking-widest px-2 mb-3 font-mono">Agents</div>
        {AGENT_META.map((agent) => {
          const state = agentStates[agent.key] || "idle";
          return (
            <div key={agent.key}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 border transition-all duration-200 ${
                state !== "idle"
                  ? "bg-navy-600 border-border text-slate-300"
                  : "bg-transparent border-transparent text-slate-500"
              }`}
            >
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${DOT_COLORS[state] || DOT_COLORS.idle}`} />
              <div>
                <div className="text-xs font-semibold leading-none mb-0.5">{agent.label}</div>
                <div className="text-[10px] text-slate-600 font-mono">{agent.desc}</div>
              </div>
              {state === "running" && <div className="ml-auto w-3.5 h-3.5 border-2 border-slate-600 border-t-accent-blue rounded-full animate-spin-slow" />}
              {state === "success" && <div className="ml-auto text-accent-green text-xs">✓</div>}
              {state === "error"   && <div className="ml-auto text-accent-red   text-xs">✗</div>}
            </div>
          );
        })}
      </div>
      <div className="px-5 py-4 border-t border-border">
        <div className="text-[10px] text-slate-700 uppercase tracking-widest mb-2 font-mono">Session</div>
        <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
          <div className={`w-1.5 h-1.5 rounded-full ${
            sidebarStatus === "running" ? "bg-accent-amber animate-pulse"
            : sidebarStatus === "success" ? "bg-accent-green"
            : sidebarStatus === "error"   ? "bg-accent-red"
            : "bg-slate-700"
          }`} />
          {sidebarStatus === "running" ? "Running agents..."
           : sidebarStatus === "success" ? "Complete"
           : sidebarStatus === "error"   ? "Failed"
           : "Ready"}
        </div>
      </div>
    </>
  );

  if (embedded) return <div className="flex flex-col flex-1 overflow-hidden">{inner}</div>;

  return (
    <aside className="w-64 bg-navy-800 border-r border-border flex flex-col">
      <div className="px-5 py-5 border-b border-border">
        <div className="text-[10px] text-slate-600 uppercase tracking-widest mb-1 font-mono">Agentic AI</div>
        <div className="text-base font-bold text-accent-blue font-mono tracking-tight">Pipeline Debugger</div>
      </div>
      {inner}
    </aside>
  );
}
