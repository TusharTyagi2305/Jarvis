import React, { useRef, useEffect } from "react";
import type { ChatMessage } from "../../types/jarvis";
import "./ChatPanel.css";

interface ChatPanelProps {
  messages: ChatMessage[];
  onConfirmToken?: (token: string, originalQuery: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onConfirmToken }) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel hud-panel">
      <div className="panel-header">
        <span className="panel-icon">💬</span>
        <h3 className="panel-title">CONVERSATION STREAM</h3>
      </div>

      <div className="chat-list">
        {messages.length === 0 ? (
          <div className="chat-empty">No conversation active. Type a command below.</div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`chat-message msg-${msg.sender}`}>
              <div className="msg-meta">
                <span className="msg-sender">{msg.sender === "user" ? "USER" : "JARVIS"}</span>
                <span className="msg-time">{msg.timestamp}</span>
              </div>
              <div className="msg-body">{msg.text}</div>

              {msg.pendingConfirmation && onConfirmToken && (
                <div className="chat-confirmation-box">
                  <div className="conf-warn">⚠ Confirmation Required</div>
                  <div className="conf-msg">{msg.pendingConfirmation.message}</div>
                  <button
                    className="hud-btn"
                    onClick={() => onConfirmToken(msg.pendingConfirmation!.confirmation_id, msg.text)}
                  >
                    Confirm Action Now
                  </button>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={scrollRef} />
      </div>
    </div>
  );
};
