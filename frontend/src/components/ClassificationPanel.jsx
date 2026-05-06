import ResultCard, { EmptyState, LoadingState } from "./ResultCard";
import FeedbackButtons from "./FeedbackButtons";

const SEV_STYLES = {
  critical: "bg-red-950 text-accent-red border border-red-900/50",
  high:     "bg-amber-950 text-accent-amber border border-amber-900/50",
  medium:   "bg-blue-950 text-blue-400 border border-blue-900/50",
  low:      "bg-green-950 text-accent-green border border-green-900/50",
};

export default function ClassificationPanel({ status, data, pipelineId, sessionId }) {
  return (
    <ResultCard title="Error Classification" icon="🔍" status={status}>
      {status === "pending" && <EmptyState icon="🔍" text={"Waiting for error\nclassification"} />}
      {status === "running" && <LoadingState message="Classifying failure type..." />}
      {status === "error"   && <div className="text-accent-red font-mono text-xs">{data?.error || "Agent failed"}</div>}
      {status === "success" && data && (
        <div className="animate-slide-up space-y-3">
          <div className={`inline-flex items-center gap-2 text-[10px] font-semibold px-2 py-1 rounded ${SEV_STYLES[data.severity] || SEV_STYLES.medium}`}>
            {(data.severity || "").toUpperCase()} · {data.confidence || "—"}% confidence
          </div>
          <div className="text-sm font-bold text-slate-200 font-mono">
            {(data.error_type || "").replace(/_/g, " ").toUpperCase()}
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">{data.root_cause}</div>
          {data.indicators?.length > 0 && (
            <div>
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-1.5">Indicators</div>
              {data.indicators.map((ind, i) => (
                <div key={i} className="text-[11px] text-slate-500 font-mono mb-1">→ {ind}</div>
              ))}
            </div>
          )}
          {data.affected_layer && (
            <div className="text-[10px] text-slate-600 font-mono">
              Layer: <span className="bg-navy-600 border border-border text-slate-400 px-1.5 py-0.5 rounded">{data.affected_layer}</span>
            </div>
          )}
          {pipelineId && (
            <FeedbackButtons pipelineId={pipelineId} sessionId={sessionId} type="classification" />
          )}
        </div>
      )}
    </ResultCard>
  );
}
