import ResultCard, { EmptyState, LoadingState } from "./ResultCard";
import FeedbackButtons from "./FeedbackButtons";

const CHECK_STYLES = {
  pass: { cls: "bg-green-950 text-accent-green border-green-900/50", icon: "✓" },
  warn: { cls: "bg-amber-950 text-accent-amber border-amber-900/50", icon: "!" },
  fail: { cls: "bg-red-950 text-accent-red border-red-900/50",       icon: "✗" },
};

export default function FixPanel({ status, data, pipelineId, sessionId }) {
  return (
    <ResultCard title="Generated Fix & Validation" icon="🔧" status={status}>
      {status === "pending" && <EmptyState icon="🔧" text={"Fix will be generated\nafter analysis"} />}
      {status === "running" && <LoadingState message="Generating validated remediation..." />}
      {status === "error"   && <div className="text-accent-red font-mono text-xs">{data?.error || "Agent failed"}</div>}
      {status === "success" && data && (
        <div className="animate-slide-up space-y-4">
          <div>
            <div className="text-sm font-bold text-slate-200 font-mono">{data.title}</div>
            <div className="text-[10px] text-slate-600 mt-0.5 font-mono">
              Est. resolution: <span className="text-accent-blue">{data.estimated_time}</span>
            </div>
          </div>
          <div className="bg-navy-800 border border-border rounded p-3 space-y-3">
            {(data.steps || []).map((step) => (
              <div key={step.step_num} className="flex gap-3 text-[11px]">
                <span className="text-accent-blue font-bold font-mono flex-shrink-0">{step.step_num}.</span>
                <div>
                  <div className="text-slate-300 mb-1">{step.action}</div>
                  {step.code_hint && (
                    <div className="font-mono text-accent-green bg-navy-900 px-2 py-1.5 rounded text-[10px] mt-1 border border-border">
                      {step.code_hint}
                    </div>
                  )}
                  {step.estimated_time && (
                    <div className="text-[10px] text-slate-600 mt-1">{step.estimated_time}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {data.validation_checks?.length > 0 && (
            <div>
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">Validation Checks</div>
              {data.validation_checks.map((v, i) => {
                const style = CHECK_STYLES[v.result] || CHECK_STYLES.warn;
                return (
                  <div key={i} className="flex items-center gap-2 py-1.5 text-[11px] font-mono">
                    <span className={`w-4 h-4 rounded-full border flex items-center justify-center text-[9px] font-bold flex-shrink-0 ${style.cls}`}>
                      {style.icon}
                    </span>
                    <span className="flex-1 text-slate-400">{v.check}</span>
                    {v.note && <span className="text-slate-600 text-[10px]">{v.note}</span>}
                  </div>
                );
              })}
            </div>
          )}
          {data.rollback_plan && (
            <div className="text-[11px] text-slate-500 font-mono px-3 py-2 bg-navy-800 rounded border-l-2 border-accent-blue">
              <strong className="text-slate-400">Rollback:</strong> {data.rollback_plan}
            </div>
          )}
          {data.preventive_measures?.length > 0 && (
            <div>
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">Prevention</div>
              {data.preventive_measures.map((p, i) => (
                <div key={i} className="text-[11px] text-slate-500 font-mono mb-1">↗ {p}</div>
              ))}
            </div>
          )}
          {pipelineId && (
            <FeedbackButtons pipelineId={pipelineId} sessionId={sessionId} type="fix" />
          )}
        </div>
      )}
    </ResultCard>
  );
}
