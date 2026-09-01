import React from "react";
import "./TaskExecutionPanel.css";

export interface TaskStepInfo {
  id: string;
  description: string;
  status: string;
  tool?: string;
  error?: string;
}

interface TaskExecutionPanelProps {
  goal?: string;
  status?: string;
  steps?: TaskStepInfo[];
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
}

export const TaskExecutionPanel: React.FC<TaskExecutionPanelProps> = ({
  goal = "Inspect & verify project workspace",
  status = "IDLE",
  steps = [],
  onPause,
  onResume,
  onCancel
}) => {
  const completedCount = steps.filter((s) => s.status === "COMPLETED" || s.status === "SKIPPED").length;
  const totalCount = steps.length || 1;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  const getStatusBadge = (st: string) => {
    switch (st.toUpperCase()) {
      case "COMPLETED":
        return <span className="step-status completed">✓</span>;
      case "RUNNING":
        return <span className="step-status running">●</span>;
      case "FAILED":
        return <span className="step-status failed">✕</span>;
      case "RETRYING":
        return <span className="step-status retrying">⟳</span>;
      case "PAUSED":
        return <span className="step-status paused">⏸</span>;
      default:
        return <span className="step-status pending">○</span>;
    }
  };

  return (
    <div className="task-panel hud-panel">
      <div className="hud-header">
        <span className="panel-icon">⚙️</span>
        <span className="panel-title">AUTONOMOUS TASK GRAPH</span>
        <span className={`task-status-badge ${status.toLowerCase()}`}>{status}</span>
      </div>

      <div className="task-goal-box">
        <span className="goal-label">GOAL:</span>
        <span className="goal-text">{goal}</span>
      </div>

      {/* Animated Progress Bar */}
      <div className="task-progress-container">
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
        </div>
        <span className="progress-text">{progressPercent}%</span>
      </div>

      {/* Step List */}
      <div className="task-steps-checklist">
        {steps.length === 0 ? (
          <div className="no-steps">No active task plan executing.</div>
        ) : (
          steps.map((step) => (
            <div key={step.id} className={`task-step-item ${step.status.toLowerCase()}`}>
              {getStatusBadge(step.status)}
              <div className="step-details">
                <span className="step-desc">{step.description}</span>
                {step.tool && <span className="step-tool">[{step.tool}]</span>}
                {step.error && <div className="step-error-text">{step.error}</div>}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Task Controls */}
      <div className="task-action-controls">
        {status === "PAUSED" ? (
          <button className="hud-btn resume-btn" onClick={onResume}>
            ▶ RESUME
          </button>
        ) : (
          <button className="hud-btn pause-btn" onClick={onPause} disabled={status === "IDLE" || status === "COMPLETED"}>
            ⏸ PAUSE
          </button>
        )}
        <button className="hud-btn cancel-btn" onClick={onCancel} disabled={status === "IDLE" || status === "COMPLETED"}>
          ✕ CANCEL
        </button>
      </div>
    </div>
  );
};
