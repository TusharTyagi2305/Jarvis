import React from "react";
import "./ScreenVisionPanel.css";

export interface VisionElementInfo {
  type: string;
  text: string;
  x: number;
  y: number;
  confidence: number;
}

interface ScreenVisionPanelProps {
  status: string;
  activeWindow: string;
  elements: VisionElementInfo[];
  description: string;
}

export const ScreenVisionPanel: React.FC<ScreenVisionPanelProps> = ({
  status = "IDLE",
  activeWindow = "Windows Desktop",
  elements = [],
  description = "No visual analysis performed yet."
}) => {
  return (
    <div className="vision-panel hud-panel">
      <div className="hud-header">
        <span className="panel-icon">👁️</span>
        <span className="panel-title">SCREEN VISION</span>
        <span className={`vision-status-tag ${status.toLowerCase()}`}>
          {status}
        </span>
      </div>

      <div className="vision-info-card">
        <div className="vision-row">
          <span className="v-label">Window:</span>
          <span className="v-val window-val">{activeWindow}</span>
        </div>
        <div className="vision-row">
          <span className="v-label">Summary:</span>
          <span className="v-val desc-val">{description}</span>
        </div>
      </div>

      {elements.length > 0 && (
        <div className="vision-elements-container">
          <div className="v-header">Detected Elements ({elements.length})</div>
          <div className="v-elements-list">
            {elements.slice(0, 5).map((el, idx) => (
              <div key={idx} className="v-element-chip">
                <span className="el-type">{el.type.toUpperCase()}</span>
                <span className="el-text">{el.text || "Unlabeled"}</span>
                <span className="el-coords">({el.x}, {el.y})</span>
                <span className="el-conf">{(el.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
