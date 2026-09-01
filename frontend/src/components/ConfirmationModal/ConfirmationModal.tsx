import React, { useEffect } from "react";
import type { ConfirmationRequest } from "../../types/jarvis";
import "./ConfirmationModal.css";

interface ConfirmationModalProps {
  request: ConfirmationRequest;
  onConfirm: (token: string) => void;
  onCancel: () => void;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({ request, onConfirm, onCancel }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  return (
    <div className="modal-backdrop">
      <div className="confirmation-dialog hud-panel">
        <div className="dialog-header">
          <span className="warning-icon">⚠️</span>
          <h3>CONFIRMATION REQUIRED</h3>
        </div>

        <div className="dialog-body">
          <p className="dialog-message">
            JARVIS requests your permission to execute action:
          </p>
          <div className="dialog-detail-card">
            <div className="detail-row">
              <span className="label">TOOL:</span>
              <span className="value tool-name">{request.tool_name}</span>
            </div>
            <div className="detail-row">
              <span className="label">RISK TIER:</span>
              <span className={`value risk-badge risk-${request.risk_level.toLowerCase()}`}>
                {request.risk_level}
              </span>
            </div>
            {request.parameters && (
              <div className="detail-row params-row">
                <span className="label">TARGET PARAMS:</span>
                <pre className="params-json">{JSON.stringify(request.parameters, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>

        <div className="dialog-actions">
          <button className="hud-btn hud-btn-cancel" onClick={onCancel}>
            CANCEL
          </button>
          <button className="hud-btn" onClick={() => onConfirm(request.confirmation_id)}>
            CONFIRM ACTION
          </button>
        </div>
      </div>
    </div>
  );
};
