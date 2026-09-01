import { useState, useEffect } from "react";
import type { TelemetryData } from "../types/jarvis";
import { fetchSystemTelemetry } from "../services/api";

export function useTelemetry(pollIntervalMs: number = 4000) {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadTelemetry() {
      try {
        const data = await fetchSystemTelemetry();
        if (isMounted) {
          setTelemetry(data);
          setError(null);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to fetch telemetry");
        }
      }
    }

    loadTelemetry();
    const interval = setInterval(loadTelemetry, pollIntervalMs);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [pollIntervalMs]);

  return { telemetry, error, setTelemetry };
}
