import type { TelemetryData } from "../types/jarvis";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function sendCommand(command: string) {
  const response = await fetch(`${API_BASE_URL}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}

export async function confirmAction(token: string, original_query: string) {
  const response = await fetch(`${API_BASE_URL}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, original_query }),
  });
  if (!response.ok) {
    throw new Error(`Confirmation error: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSystemTelemetry(): Promise<TelemetryData> {
  const response = await fetch(`${API_BASE_URL}/system`);
  if (!response.ok) {
    throw new Error(`Telemetry error: ${response.statusText}`);
  }
  const result = await response.json();
  return result.data;
}

export async function fetchAuditHistory(limit: number = 50) {
  const response = await fetch(`${API_BASE_URL}/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`History error: ${response.statusText}`);
  }
  return response.json();
}
