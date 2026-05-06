const STATUS_STYLES = {
  pending: "bg-navy-600 text-slate-600",
  running: "bg-amber-950 text-accent-amber",
  success: "bg-green-950 text-accent-green",
  error: "bg-red-950 text-accent-red",
};

export default function ResultCard({ title, icon, status, children }) {
  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <div className="card-title">
          <span>{icon}</span> {title}
        </div>
        <span className={`badge text-[10px] font-semibold px-2 py-0.5 rounded ${STATUS_STYLES[status] || STATUS_STYLES.pending}`}>
          {status === "running" ? "Running" : status === "success" ? "Complete" : status === "error" ? "Error" : "Pending"}
        </span>
      </div>
      <div className="p-4 text-xs leading-relaxed text-slate-400 min-h-[80px]">
        {children}
      </div>
    </div>
  );
}

export function EmptyState({ icon, text }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-2 text-slate-700">
      <div className="text-3xl opacity-40">{icon}</div>
      <div className="text-[11px] text-center leading-relaxed font-mono">{text}</div>
    </div>
  );
}

export function LoadingState({ message }) {
  return (
    <div className="flex items-center gap-3 text-slate-600 font-mono text-xs">
      <div className="w-4 h-4 border-2 border-slate-700 border-t-accent-blue rounded-full animate-spin-slow flex-shrink-0" />
      {message}
    </div>
  );
}
