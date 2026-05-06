export default function InputPanel({ form, onChange }) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="text-accent-blue text-base">⬡</span>
          Failure Input
        </div>
        <span className="badge bg-navy-500 text-blue-400 border border-blue-900/50">
          4-Agent Pipeline
        </span>
      </div>
      <div className="p-4 grid grid-cols-2 gap-4">
        <div>
          <div className="field-label">Pipeline ID</div>
          <input
            className="field-input"
            value={form.pipeline_id}
            onChange={(e) => onChange("pipeline_id", e.target.value)}
            placeholder="etl_sales_daily_v2"
          />
        </div>
        <div>
          <div className="field-label">Log Source</div>
          <select
            className="field-input cursor-pointer"
            value={form.log_source}
            onChange={(e) => onChange("log_source", e.target.value)}
          >
            <option value="inline">Inline (paste below)</option>
            <option value="airflow">Airflow API</option>
            <option value="s3">AWS S3</option>
          </select>
        </div>
        <div className="col-span-2">
          <div className="field-label">Error Logs *</div>
          <textarea
            className="field-input resize-y min-h-[96px]"
            value={form.error_logs}
            onChange={(e) => onChange("error_logs", e.target.value)}
            placeholder="Paste error message / stack trace here..."
          />
        </div>
        <div className="col-span-2">
          <div className="field-label">Pipeline Config / Context (optional)</div>
          <textarea
            className="field-input resize-y min-h-[64px]"
            value={form.pipeline_config}
            onChange={(e) => onChange("pipeline_config", e.target.value)}
            placeholder="Schema info, resource limits, upstream tables, DAG structure..."
          />
        </div>
      </div>
    </div>
  );
}
