import { useState, useRef, useCallback } from "react";
import { openDebugStream } from "../services/api";

const INITIAL_STATES = {
  log_fetch:      "idle",
  metadata:       "idle",
  classification: "idle",
  dependency:     "idle",
  fix:            "idle",
};

export function useStreamDebug() {
  const [agentStates,  setAgentStates]  = useState(INITIAL_STATES);
  const [agentTimings, setAgentTimings] = useState({});
  const [agentData,    setAgentData]    = useState({});
  const [streaming,    setStreaming]    = useState(false);
  const [done,         setDone]         = useState(false);
  const [error,        setError]        = useState(null);
  const streamRef = useRef(null);

  const reset = useCallback(() => {
    streamRef.current?.close();
    setAgentStates(INITIAL_STATES);
    setAgentTimings({});
    setAgentData({});
    setStreaming(false);
    setDone(false);
    setError(null);
  }, []);

  const startStream = useCallback((payload) => {
    reset();
    setStreaming(true);

    streamRef.current = openDebugStream(payload, {
      onEvent: (event) => {
        const { step, status, data, duration_ms } = event;

        if (step === "pipeline") return; // pipeline-level events, skip

        setAgentStates((prev) => ({
          ...prev,
          [step]: status === "running" ? "running"
                : status === "success" ? "success"
                : status === "error"   ? "error"
                : prev[step],
        }));

        if (duration_ms && status !== "running") {
          setAgentTimings((prev) => ({ ...prev, [step]: duration_ms }));
        }

        if (status !== "running" && data && Object.keys(data).length > 0) {
          setAgentData((prev) => ({ ...prev, [step]: data }));
        }
      },

      onError: (err) => {
        setError(err.message || "Stream error");
        setStreaming(false);
        // Mark running agents as error
        setAgentStates((prev) =>
          Object.fromEntries(
            Object.entries(prev).map(([k, v]) => [k, v === "running" ? "error" : v])
          )
        );
      },

      onDone: () => {
        setStreaming(false);
        setDone(true);
      },
    });
  }, [reset]);

  const stopStream = useCallback(() => {
    streamRef.current?.close();
    setStreaming(false);
  }, []);

  return {
    agentStates,
    agentTimings,
    agentData,
    streaming,
    done,
    error,
    startStream,
    stopStream,
    reset,
  };
}
