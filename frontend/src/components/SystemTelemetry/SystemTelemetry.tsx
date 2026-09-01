import React from "react";
import type { TelemetryData } from "../../types/jarvis";
import "./SystemTelemetry.css";

interface SystemTelemetryProps {
  telemetry: TelemetryData | null;
}

export const SystemTelemetry: React.FC<SystemTelemetryProps> = ({ telemetry }) => {
  const cpu = telemetry ? telemetry.cpu_usage_percent : 0;
  const ram = telemetry ? telemetry.memory_used_percent : 0;
  const disk = telemetry ? telemetry.disk_used_percent : 0;
  const battery = telemetry && telemetry.battery ? telemetry.battery.percent : null;
  const osInfo = telemetry ? telemetry.os : "Windows Desktop";

  return (
    <div className="system-telemetry hud-panel">
      <div className="panel-header">
        <span className="panel-icon">⚡</span>
        <h3 className="panel-title">SYSTEM TELEMETRY</h3>
      </div>

      <div className="telemetry-grid">
        {/* CPU Meter */}
        <div className="telemetry-card">
          <div className="card-top">
            <span className="card-label">CPU</span>
            <span className="card-value">{cpu}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill fill-cpu" style={{ width: `${cpu}%` }}></div>
          </div>
        </div>

        {/* RAM Meter */}
        <div className="telemetry-card">
          <div className="card-top">
            <span className="card-label">RAM MEMORY</span>
            <span className="card-value">{ram}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill fill-ram" style={{ width: `${ram}%` }}></div>
          </div>
        </div>

        {/* Disk Space Meter */}
        <div className="telemetry-card">
          <div className="card-top">
            <span className="card-label">STORAGE</span>
            <span className="card-value">{disk}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill fill-disk" style={{ width: `${disk}%` }}></div>
          </div>
        </div>

        {/* Battery Status */}
        <div className="telemetry-card">
          <div className="card-top">
            <span className="card-label">BATTERY</span>
            <span className="card-value">{battery !== null ? `${battery}%` : "AC POWER"}</span>
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill fill-battery"
              style={{ width: `${battery !== null ? battery : 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="os-badge">
        <span className="os-label">HOST OS:</span>
        <span className="os-value">{osInfo}</span>
      </div>
    </div>
  );
};
