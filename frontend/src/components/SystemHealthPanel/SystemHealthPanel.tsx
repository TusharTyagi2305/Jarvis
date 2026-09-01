import React from "react";
import "./SystemHealthPanel.css";

export interface SubsystemHealthInfo {
  core: boolean;
  voice: boolean;
  vision: boolean;
  browser: boolean;
  memory: boolean;
  llm: boolean;
}

interface SystemHealthPanelProps {
  version?: string;
  health?: SubsystemHealthInfo;
}

export const SystemHealthPanel: React.FC<SystemHealthPanelProps> = ({
  version = "1.0.0",
  health = {
    core: true,
    voice: true,
    vision: true,
    browser: true,
    memory: true,
    llm: true
  }
}) => {
  return (
    <div className="health-panel hud-panel">
      <div className="hud-header">
        <span className="panel-icon">💻</span>
        <span className="panel-title">SYSTEM DIAGNOSTICS</span>
        <span className="version-badge">JARVIS v{version}</span>
      </div>

      <div className="subsystems-grid">
        <div className="subsystem-item">
          <span className="sub-name">CORE</span>
          <span className={`sub-status ${health.core ? "ready" : "degraded"}`}>
            {health.core ? "● ONLINE" : "○ OFFLINE"}
          </span>
        </div>

        <div className="subsystem-item">
          <span className="sub-name">VOICE</span>
          <span className={`sub-status ${health.voice ? "ready" : "degraded"}`}>
            {health.voice ? "● READY" : "○ DEGRADED"}
          </span>
        </div>

        <div className="subsystem-item">
          <span className="sub-name">VISION</span>
          <span className={`sub-status ${health.vision ? "ready" : "degraded"}`}>
            {health.vision ? "● READY" : "○ DEGRADED"}
          </span>
        </div>

        <div className="subsystem-item">
          <span className="sub-name">BROWSER</span>
          <span className={`sub-status ${health.browser ? "ready" : "degraded"}`}>
            {health.browser ? "● READY" : "○ DEGRADED"}
          </span>
        </div>

        <div className="subsystem-item">
          <span className="sub-name">MEMORY</span>
          <span className={`sub-status ${health.memory ? "ready" : "degraded"}`}>
            {health.memory ? "● READY" : "○ DEGRADED"}
          </span>
        </div>

        <div className="subsystem-item">
          <span className="sub-name">AI / LLM</span>
          <span className={`sub-status ${health.llm ? "ready" : "degraded"}`}>
            {health.llm ? "● CONNECTED" : "○ DISCONNECTED"}
          </span>
        </div>
      </div>
    </div>
  );
};
