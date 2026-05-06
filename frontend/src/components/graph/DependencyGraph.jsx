import { useEffect, useRef, useMemo } from "react";

// ─── Constants ────────────────────────────────────────────────────────────────
const W = 700, H = 340;
const NODE_R = 28;

const ROLE_STYLE = {
  failed:     { fill: "#2a0d14", stroke: "#e85d75", text: "#ffb0bc", icon: "💥" },
  upstream:   { fill: "#0d1a2a", stroke: "#3b72f8", text: "#93b4ff", icon: "⬆" },
  downstream: { fill: "#0a1a14", stroke: "#3dd68c", text: "#a0f0c0", icon: "⬇" },
};

const IMPACT_GLOW = {
  high:   "drop-shadow(0 0 8px rgba(232,93,117,0.6))",
  medium: "drop-shadow(0 0 6px rgba(245,166,35,0.4))",
  low:    "drop-shadow(0 0 4px rgba(61,214,140,0.3))",
  none:   "none",
};

const TYPE_ICON = {
  pipeline:  "🔄", table: "🗄", api: "🌐", kafka: "📨",
  s3:        "🪣", dashboard: "📊", ml_model: "🤖",
};

// ─── Layout: position nodes in columns ───────────────────────────────────────
function layoutNodes(nodes) {
  if (!nodes?.length) return [];

  const upstream   = nodes.filter((n) => n.role === "upstream");
  const failed     = nodes.filter((n) => n.role === "failed");
  const downstream = nodes.filter((n) => n.role === "downstream");

  const col = (items, x) =>
    items.map((n, i) => ({
      ...n,
      x,
      y: H / 2 + (i - (items.length - 1) / 2) * 80,
    }));

  return [
    ...col(upstream,   W * 0.18),
    ...col(failed,     W * 0.50),
    ...col(downstream, W * 0.82),
  ];
}

// ─── Component ───────────────────────────────────────────────────────────────
export default function DependencyGraph({ graph }) {
  const svgRef = useRef(null);

  const { positioned, edgeMap } = useMemo(() => {
    if (!graph?.nodes?.length) return { positioned: [], edgeMap: {} };
    const pos = layoutNodes(graph.nodes);
    const map = Object.fromEntries(pos.map((n) => [n.id, n]));
    return { positioned: pos, edgeMap: map };
  }, [graph]);

  if (!graph?.nodes?.length) {
    return (
      <div className="flex items-center justify-center h-40 text-slate-700 text-xs font-mono">
        Dependency graph will appear here after analysis
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ maxHeight: 340, minHeight: 220 }}
        className="select-none"
      >
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#2a3a60" />
          </marker>
          <marker id="arrow-red" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#e85d75" />
          </marker>
          <filter id="glow-red">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Column labels */}
        {[
          { x: W * 0.18, label: "UPSTREAM" },
          { x: W * 0.50, label: "FAILED" },
          { x: W * 0.82, label: "DOWNSTREAM" },
        ].map(({ x, label }) => (
          <text key={label} x={x} y={18} textAnchor="middle"
            fontSize={9} fill="#2a3a60" fontFamily="monospace" letterSpacing={2}>
            {label}
          </text>
        ))}

        {/* Edges */}
        {(graph.edges || []).map((edge, i) => {
          const src = edgeMap[edge.source];
          const tgt = edgeMap[edge.target];
          if (!src || !tgt) return null;

          const isHighRisk =
            tgt?.impact === "high" || src?.role === "failed" || tgt?.role === "failed";

          // Offset endpoints to node perimeter
          const dx = tgt.x - src.x, dy = tgt.y - src.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const x1 = src.x + (dx / dist) * (NODE_R + 2);
          const y1 = src.y + (dy / dist) * (NODE_R + 2);
          const x2 = tgt.x - (dx / dist) * (NODE_R + 6);
          const y2 = tgt.y - (dy / dist) * (NODE_R + 6);

          // Bezier control point
          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2 - 20;

          return (
            <g key={i}>
              <path
                d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`}
                fill="none"
                stroke={isHighRisk ? "#e85d75" : "#2a3a60"}
                strokeWidth={isHighRisk ? 1.5 : 1}
                strokeDasharray={isHighRisk ? "none" : "4 3"}
                markerEnd={`url(#${isHighRisk ? "arrow-red" : "arrow"})`}
                opacity={0.7}
              />
              {edge.label && (
                <text x={mx} y={my - 5} textAnchor="middle"
                  fontSize={8} fill="#3a4a70" fontFamily="monospace">
                  {edge.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {positioned.map((node) => {
          const style = ROLE_STYLE[node.role] || ROLE_STYLE.downstream;
          const icon  = TYPE_ICON[node.type] || "📦";
          const glow  = IMPACT_GLOW[node.impact] || "none";

          return (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
              {/* Outer ring for high-impact nodes */}
              {node.impact === "high" && (
                <circle r={NODE_R + 6} fill="none"
                  stroke={node.role === "failed" ? "#e85d75" : "#f5a623"}
                  strokeWidth={1} strokeDasharray="3 3" opacity={0.4} />
              )}
              {/* Main circle */}
              <circle
                r={NODE_R}
                fill={style.fill}
                stroke={style.stroke}
                strokeWidth={node.role === "failed" ? 2.5 : 1.5}
                style={{ filter: node.role === "failed" ? "drop-shadow(0 0 10px rgba(232,93,117,0.5))" : glow }}
              />
              {/* Icon */}
              <text textAnchor="middle" dominantBaseline="central"
                y={-6} fontSize={14} style={{ userSelect: "none" }}>
                {icon}
              </text>
              {/* Role badge for failed */}
              {node.role === "failed" && (
                <text textAnchor="middle" y={8} fontSize={9}
                  fill="#e85d75" fontFamily="monospace" fontWeight="700">
                  FAILED
                </text>
              )}
              {/* Label below node */}
              <text textAnchor="middle" y={NODE_R + 14} fontSize={9}
                fill={style.text} fontFamily="monospace"
                style={{ maxWidth: 80 }}>
                {node.label?.length > 16 ? node.label.slice(0, 15) + "…" : node.label}
              </text>
              {/* Impact badge */}
              {node.impact && node.impact !== "none" && (
                <text textAnchor="middle" y={NODE_R + 24} fontSize={7.5}
                  fill={node.impact === "high" ? "#e85d75" : node.impact === "medium" ? "#f5a623" : "#3dd68c"}
                  fontFamily="monospace" fontWeight="600">
                  {node.impact.toUpperCase()}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-2 justify-center text-[10px] font-mono text-slate-600">
        {[
          { color: "#3b72f8", label: "Upstream" },
          { color: "#e85d75", label: "Failed" },
          { color: "#3dd68c", label: "Downstream" },
          { color: "#f5a623", label: "High impact" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
