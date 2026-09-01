import React, { useEffect, useRef } from "react";
import type { ActivityItem } from "../../types/jarvis";
import "./ActivityFeed.css";

interface ActivityFeedProps {
  activities: ActivityItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities }) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activities]);

  const getStatusBadge = (status: ActivityItem["status"]) => {
    switch (status) {
      case "success": return <span className="feed-status-dot dot-success">✓</span>;
      case "warning": return <span className="feed-status-dot dot-warning">⚠</span>;
      case "error": return <span className="feed-status-dot dot-error">✕</span>;
      case "pending": return <span className="feed-status-dot dot-pending">●</span>;
      default: return <span className="feed-status-dot dot-info">●</span>;
    }
  };

  return (
    <div className="activity-feed hud-panel">
      <div className="panel-header">
        <span className="panel-icon">📡</span>
        <h3 className="panel-title">REAL-TIME TASK & TOOL FEED</h3>
      </div>

      <div className="feed-list">
        {activities.length === 0 ? (
          <div className="feed-empty">System ready. Waiting for task commands...</div>
        ) : (
          activities.map((item) => (
            <div key={item.id} className={`feed-item item-${item.status}`}>
              <div className="feed-item-header">
                {getStatusBadge(item.status)}
                <span className="feed-time">{item.timestamp}</span>
                <span className="feed-item-title">{item.title}</span>
              </div>
              {item.details && <div className="feed-item-details">{item.details}</div>}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
