import ResultCard, { EmptyState, LoadingState } from "./ResultCard";

const STATUS_COLOR = {
  success: "text-accent-green",
  failed: "text-accent-red",
  running: "text-accent-amber",
};

export default function MetadataPanel({ status, data }) {
  return (
    <ResultCard title="Metadata & Run History" icon="📋" status={status}>
      {status === "pending" && <EmptyState icon="📋" text={"Run agents to fetch\npipeline metadata"} />}
      {status === "running" && <LoadingState message="Fetching pipeline metadata..." />}
      {status === "error" && (
        <div className="text-accent-red font-mono text-xs">{data?.error || "Agent failed"}</div>
      )}
      {status === "success" && data && (
        <div className="animate-slide-up space-y-3">
          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { val: data.fail_count_7d ?? "—", lbl: "Failures (7d)" },
              { val: `${data.avg_runtime_min ?? "—"}m`, lbl: "Avg Runtime" },
              { val: data.data_volume ?? "—", lbl: "Volume" },
            ].map((m) => (
              <div key={m.lbl} className="bg-navy-800 border border-border rounded p-2.5">
                <div className="text-sm font-bold text-accent-blue font-mono">{m.val}</div>
                <div className="text-[10px] text-slate-600 mt-0.5">{m.lbl}</div>
              </div>
            ))}
          </div>

          {/* Meta info */}
          <div className="text-[11px] font-mono space-y-1">
            <span className="text-slate-600">Owner:</span>{" "}
            <span className="text-accent-blue">{data.owner || "—"}</span>
            {"  ·  "}
            <span className="text-slate-600">Env:</span>{" "}
            <span className="text-accent-blue">{data.environment || "prod"}</span>
            {"  ·  "}
            <span className="text-slate-600">Schedule:</span>{" "}
            <span className="text-accent-blue">{data.schedule || "—"}</span>
          </div>

          {/* Tags */}
          {data.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {data.tags.map((t) => (
                <span key={t} className="text-[10px] bg-navy-600 border border-border text-slate-500 px-2 py-0.5 rounded font-mono">
                  {t}
                </span>
              ))}
            </div>
          )}

          {/* Run history */}
          <div>
            <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">Recent Runs</div>
            <div className="space-y-1">
              {(data.run_history || []).slice(0, 5).map((r, i) => (
                <div key={i} className="flex items-center gap-2 text-[11px] font-mono py-1 border-b border-border/50">
                  <div
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{
                      background:
                        r.status === "success" ? "#3dd68c" : r.status === "running" ? "#f5a623" : "#e85d75",
                    }}
                  />
                  <span className="text-slate-600 w-28 flex-shrink-0">{String(r.timestamp).substring(5, 16)}</span>
                  <span className={STATUS_COLOR[r.status] || "text-slate-400"}>{r.status}</span>
                  <span className="ml-auto text-slate-600">
                    {r.duration_min}m · {(r.rows_processed || 0).toLocaleString()} rows
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </ResultCard>
  );
}
