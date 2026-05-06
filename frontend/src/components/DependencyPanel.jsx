import ResultCard, { EmptyState, LoadingState } from "./ResultCard";
import DependencyGraph from "./graph/DependencyGraph";

const IMPACT_STYLES = {
  high:   "bg-red-950 text-accent-red",
  medium: "bg-amber-950 text-accent-amber",
  low:    "bg-green-950 text-accent-green",
};
const RISK_COLORS = { high: "#e85d75", medium: "#f5a623", low: "#3dd68c" };

function DepRow({ node }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/40 text-[11px] font-mono last:border-0">
      <span className="text-accent-blue">{node.name}</span>
      <span className="text-slate-600 mx-2">{node.type}</span>
      <span className={`badge text-[9px] ${IMPACT_STYLES[node.impact] || IMPACT_STYLES.medium}`}>{node.impact}</span>
    </div>
  );
}

export default function DependencyPanel({ status, data }) {
  const hasGraph = data?.graph?.nodes?.length > 0;

  return (
    <ResultCard title="Dependency Graph & Blast Radius" icon="🕸" status={status}>
      {status === "pending" && <EmptyState icon="🕸" text={"Dependency analysis\nnot yet run"} />}
      {status === "running" && <LoadingState message="Tracing dependency graph..." />}
      {status === "error"   && <div className="text-accent-red font-mono text-xs">{data?.error || "Agent failed"}</div>}
      {status === "success" && data && (
        <div className="animate-slide-up space-y-4">
          {/* Visual graph */}
          {hasGraph && (
            <div className="bg-navy-800 border border-border rounded-lg p-3">
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-3 font-mono">
                Dependency Graph
              </div>
              <DependencyGraph graph={data.graph} />
            </div>
          )}

          {/* Blast radius summary */}
          <div className="text-[11px] font-mono px-3 py-2 rounded border"
            style={{ background: "#1a1208", borderColor: "#2a2010", color: RISK_COLORS[data.cascading_risk] || "#f5a623" }}>
            Cascading Risk: <strong style={{ color: RISK_COLORS[data.cascading_risk] }}>
              {(data.cascading_risk || data.risk || "").toUpperCase()}
            </strong>{" "}— {data.blast_radius_summary}
          </div>

          {/* Upstream */}
          {data.upstream?.length > 0 && (
            <div>
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-1.5">Upstream</div>
              {data.upstream.map((u, i) => <DepRow key={i} node={u} />)}
            </div>
          )}

          {/* Downstream */}
          {data.downstream?.length > 0 && (
            <div>
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-1.5">Downstream Impact</div>
              {data.downstream.map((d, i) => <DepRow key={i} node={d} />)}
            </div>
          )}

          {data.slas_at_risk?.length > 0 && (
            <div className="text-[10px] text-accent-red font-mono">
              SLAs at risk: {data.slas_at_risk.join(" · ")}
            </div>
          )}
          {data.isolation_point && (
            <div className="text-[10px] text-slate-600 font-mono">
              Isolate at: <span className="text-accent-blue">{data.isolation_point}</span>
            </div>
          )}
        </div>
      )}
    </ResultCard>
  );
}
