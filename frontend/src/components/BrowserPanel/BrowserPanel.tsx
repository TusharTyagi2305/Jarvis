import React from "react";
import "./BrowserPanel.css";

interface TabInfo {
  index: number;
  title: string;
  url: string;
  is_active: boolean;
}

interface BrowserPanelProps {
  isConnected: boolean;
  pageTitle?: string;
  currentUrl?: string;
  currentAction?: string;
  tabs?: TabInfo[];
}

export const BrowserPanel: React.FC<BrowserPanelProps> = ({
  isConnected,
  pageTitle = "Ready",
  currentUrl = "about:blank",
  currentAction = "Idle",
  tabs = []
}) => {
  return (
    <div className="browser-panel hud-panel">
      <div className="hud-header">
        <span className="panel-icon">🌐</span>
        <span className="panel-title">BROWSER AGENT</span>
        <span className={`status-indicator ${isConnected ? "connected" : "idle"}`}>
          {isConnected ? "● Connected" : "○ Offline"}
        </span>
      </div>

      <div className="browser-info-grid">
        <div className="info-row">
          <span className="info-label">Page:</span>
          <span className="info-val title-val">{pageTitle || "Google"}</span>
        </div>
        <div className="info-row">
          <span className="info-label">URL:</span>
          <span className="info-val url-val">{currentUrl || "https://www.google.com"}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Action:</span>
          <span className="info-val action-val">{currentAction}</span>
        </div>
      </div>

      {tabs.length > 0 && (
        <div className="browser-tabs-container">
          <div className="tabs-header">Active Tabs ({tabs.length})</div>
          <div className="tabs-list">
            {tabs.map((t) => (
              <div key={t.index} className={`tab-chip ${t.is_active ? "active" : ""}`}>
                <span className="tab-num">#{t.index + 1}</span>
                <span className="tab-title">{t.title || "New Tab"}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
