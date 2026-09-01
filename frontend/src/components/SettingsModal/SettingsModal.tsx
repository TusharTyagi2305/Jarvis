import React, { useEffect } from "react";
import "./SettingsModal.css";

interface SettingsModalProps {
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="modal-backdrop">
      <div className="settings-dialog hud-panel">
        <div className="dialog-header">
          <span className="settings-icon">⚙</span>
          <h3>JARVIS SYSTEM SETTINGS</h3>
        </div>

        <div className="settings-body">
          <div className="setting-group">
            <label>ASSISTANT NAME</label>
            <input type="text" className="setting-input" defaultValue="JARVIS" disabled />
          </div>

          <div className="setting-group">
            <label>LLM PROVIDER & MODEL</label>
            <select className="setting-select" defaultValue="gemini-2.5-flash">
              <option value="gemini-2.5-flash">Google Gemini (gemini-2.5-flash)</option>
              <option value="mock">Mock Offline Provider</option>
            </select>
          </div>

          <div className="setting-group">
            <label>WAKE WORD (PHASE 3 ARCHITECTURE)</label>
            <input type="text" className="setting-input" defaultValue="Jarvis" disabled />
          </div>

          <div className="setting-group">
            <label>VOICE SYNTHESIS (PHASE 3 ARCHITECTURE)</label>
            <input type="text" className="setting-input" defaultValue="Pluggable TTS Active (Default System)" disabled />
          </div>

          <div className="setting-group">
            <label>CONFIRMATION BEHAVIOR</label>
            <select className="setting-select" defaultValue="strict">
              <option value="strict">Strict Confirmation (Require Token for CONFIRM & DANGEROUS)</option>
              <option value="auto_safe">Auto Approve Safe Actions</option>
            </select>
          </div>

          <div className="setting-group">
            <label>MAX AGENT ITERATIONS</label>
            <input type="number" className="setting-input" defaultValue={10} min={1} max={20} />
          </div>
        </div>

        <div className="dialog-actions">
          <button className="hud-btn" onClick={onClose}>
            CLOSE SETTINGS
          </button>
        </div>
      </div>
    </div>
  );
};
