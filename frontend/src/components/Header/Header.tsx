import React, { useState, useEffect } from "react";
import "./Header.css";

interface HeaderProps {
  isConnected: boolean;
  onOpenSettings: () => void;
  isMinimalMode?: boolean;
  onToggleMinimalMode?: () => void;
  isAlwaysOnTop?: boolean;
  onToggleAlwaysOnTop?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  onOpenSettings,
  isMinimalMode,
  onToggleMinimalMode,
  isAlwaysOnTop,
  onToggleAlwaysOnTop,
}) => {
  const [timeStr, setTimeStr] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="hud-header hud-panel">
      <div className="hud-header-left">
        <div className="hud-logo-icon"></div>
        <div className="hud-title-wrap">
          <h1 className="hud-title">JARVIS</h1>
          <span className="hud-subtitle">PERSONAL AI DESKTOP SYSTEM</span>
        </div>
      </div>

      <div className="hud-header-right">
        <div className={`hud-status-badge ${isConnected ? "online" : "offline"}`}>
          <span className="status-dot"></span>
          <span className="status-text">{isConnected ? "ONLINE" : "DISCONNECTED"}</span>
        </div>
        <div className="hud-clock">{timeStr}</div>

        {onToggleAlwaysOnTop && (
          <button
            className={`hud-icon-btn ${isAlwaysOnTop ? "active-toggle" : ""}`}
            onClick={onToggleAlwaysOnTop}
            title={isAlwaysOnTop ? "Always On Top: ON" : "Always On Top: OFF"}
          >
            📌
          </button>
        )}

        {onToggleMinimalMode && (
          <button
            className="hud-icon-btn"
            onClick={onToggleMinimalMode}
            title={isMinimalMode ? "Switch to Full HUD Mode" : "Switch to Minimal Mode"}
          >
            {isMinimalMode ? "📐" : "🔍"}
          </button>
        )}

        <button className="hud-icon-btn" onClick={onOpenSettings} title="Settings">
          ⚙
        </button>
      </div>
    </header>
  );
};
