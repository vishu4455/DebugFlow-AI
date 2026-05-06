import { useState } from "react";
import { submitFeedback } from "../services/api";

export default function FeedbackButtons({
  pipelineId,
  sessionId,
  type, // "classification" | "fix"
}) {
  const [voted,   setVoted]   = useState(null); // true | false | null
  const [loading, setLoading] = useState(false);
  const [sent,    setSent]    = useState(false);

  const handleVote = async (correct) => {
    if (sent || loading) return;
    setLoading(true);
    try {
      await submitFeedback({
        pipeline_id:            pipelineId,
        debug_session_id:       sessionId,
        classification_correct: type === "classification" ? correct : undefined,
        fix_useful:             type === "fix"            ? correct : undefined,
      });
      setVoted(correct);
      setSent(true);
    } catch {
      // silently fail — feedback is non-critical
      setVoted(correct);
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/40">
      <span className="text-[10px] text-slate-600 font-mono mr-1">
        {type === "classification" ? "Classification helpful?" : "Fix useful?"}
      </span>

      {sent ? (
        <span className="text-[10px] font-mono text-accent-green animate-fade-in">
          {voted ? "👍 Thanks!" : "👎 Noted"}
        </span>
      ) : (
        <>
          <button
            onClick={() => handleVote(true)}
            disabled={loading}
            className={`text-base transition-all duration-150 hover:scale-125 disabled:opacity-40 ${
              voted === true ? "opacity-100" : "opacity-50 hover:opacity-100"
            }`}
            title="Correct / Useful"
          >
            👍
          </button>
          <button
            onClick={() => handleVote(false)}
            disabled={loading}
            className={`text-base transition-all duration-150 hover:scale-125 disabled:opacity-40 ${
              voted === false ? "opacity-100" : "opacity-50 hover:opacity-100"
            }`}
            title="Incorrect / Not useful"
          >
            👎
          </button>
        </>
      )}

      {loading && (
        <div className="w-3 h-3 border border-slate-700 border-t-accent-blue rounded-full animate-spin-slow" />
      )}
    </div>
  );
}
