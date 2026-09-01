import React from "react";
import type { AgentState } from "../../types/jarvis";
import "./JarvisCore.css";

interface JarvisCoreProps {
  state: AgentState;
}

export const JarvisCore: React.FC<JarvisCoreProps> = ({ state }) => {
  const getCoreColorClass = () => {
    switch (state) {
      case "PROCESSING":
      case "PLANNING":
        return "state-processing";
      case "EXECUTING":
      case "VERIFYING":
        return "state-executing";
      case "WAITING":
      case "PAUSED":
        return "state-waiting";
      case "COMPLETED":
        return "state-completed";
      case "PERMISSION_REQUIRED":
      case "ERROR":
        return "state-error";
      case "DISABLED":
        return "state-waiting";
      case "WAKE_LISTENING":
      case "LISTENING":
      case "TRANSCRIBING":
        return "state-listening";
      case "WAKE_DETECTED":
      case "SPEAKING":
        return "state-speaking";
      case "IDLE":
      default:
        return "state-idle";
    }
  };

  return (
    <div className={`jarvis-core-container ${getCoreColorClass()}`}>
      {/* Outer Rotating HUD Ring 1 */}
      <div className="ring outer-ring animate-spin-cw">
        <svg viewBox="0 0 200 200" className="ring-svg">
          <circle cx="100" cy="100" r="90" className="svg-circle-bg" />
          <circle cx="100" cy="100" r="90" className="svg-circle-dash" strokeDasharray="30 15 60 15" />
        </svg>
      </div>

      {/* Middle Rotating HUD Ring 2 */}
      <div className="ring middle-ring animate-spin-ccw">
        <svg viewBox="0 0 160 160" className="ring-svg">
          <circle cx="80" cy="80" r="70" className="svg-circle-dash" strokeDasharray="40 10 20 10" />
        </svg>
      </div>

      {/* Inner Rotating HUD Ring 3 */}
      <div className="ring inner-ring animate-spin-cw">
        <svg viewBox="0 0 120 120" className="ring-svg">
          <circle cx="60" cy="60" r="50" className="svg-circle-dash" strokeDasharray="15 30 15 30" />
        </svg>
      </div>

      {/* Central Glowing Core Orb */}
      <div className="core-orb animate-pulse-core">
        <div className="core-center-dot"></div>
      </div>

      {/* State Label overlay */}
      <div className="core-state-label">
        <span className="state-title">{state}</span>
        <span className="state-subtitle">JARVIS CORE</span>
      </div>
    </div>
  );
};
