import { AGENT_META } from "../services/presets";

const STATE_STYLES = {
  idle: "border-slate-700 bg-navy-700 text-slate-600",
  running: "border-accent-amber bg-navy-600 text-accent-amber shadow-[0_0_14px_rgba(245,166,35,0.2)]",
  success: "border-accent-green bg-navy-700 text-accent-green shadow-[0_0_12px_rgba(61,214,140,0.15)]",
  error: "border-accent-red bg-navy-700 text-accent-red",
};

export default function AgentPipeline({ agentStates, agentTimings }) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="text-accent-blue">⬡</span>
          Agent Pipeline
        </div>
      </div>
      <div className="flex items-center gap-0 px-6 py-5 overflow-x-auto">
        {AGENT_META.map((agent, idx) => {
          const state = agentStates[agent.key] || "idle";
          const timing = agentTimings[agent.key];
          return (
            <div key={agent.key} className="flex items-center">
              {/* Node */}
              <div className="flex flex-col items-center gap-2 flex-shrink-0">
                <div
                  className={`w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl transition-all duration-300 ${STATE_STYLES[state]}`}
                >
                  {state === "running" ? (
                    <div className="w-6 h-6 border-2 border-slate-700 border-t-accent-amber rounded-full animate-spin-slow" />
                  ) : (
                    agent.icon
                  )}
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-mono leading-tight">
                    {agent.label}
                  </div>
                  {timing && (
                    <div className="text-[10px] text-accent-green font-mono mt-0.5">
                      {(timing / 1000).toFixed(1)}s
                    </div>
                  )}
                </div>
              </div>

              {/* Connector arrow */}
              {idx < AGENT_META.length - 1 && (
                <div className="flex items-center mx-2 mb-6">
                  <div className="w-8 h-px bg-slate-700" />
                  <div
                    className="border-4 border-transparent border-l-slate-700"
                    style={{ borderLeftColor: "#1e2a45" }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
