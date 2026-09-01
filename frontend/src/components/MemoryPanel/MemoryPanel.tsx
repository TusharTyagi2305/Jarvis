import React, { useState } from "react";
import "./MemoryPanel.css";

export interface MemoryRecordInfo {
  id: string;
  category: string;
  content: string;
  created_at?: number;
}

interface MemoryPanelProps {
  records?: MemoryRecordInfo[];
  onDeleteRecord?: (id: string) => void;
  onSearch?: (query: string) => void;
}

export const MemoryPanel: React.FC<MemoryPanelProps> = ({
  records = [
    { id: "1", category: "projects", content: "Main project: LearnGen AI" },
    { id: "2", category: "preferences", content: "Preferred browser: Chrome" }
  ],
  onDeleteRecord,
  onSearch
}) => {
  const [query, setQuery] = useState<string>("");
  const [selectedCat, setSelectedCat] = useState<string>("all");

  const filtered = records.filter((r) => {
    const matchesCat = selectedCat === "all" || r.category.toLowerCase() === selectedCat;
    const matchesQ = !query || r.content.toLowerCase().includes(query.toLowerCase()) || r.category.toLowerCase().includes(query.toLowerCase());
    return matchesCat && matchesQ;
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (onSearch) onSearch(val);
  };

  return (
    <div className="memory-panel hud-panel">
      <div className="hud-header">
        <span className="panel-icon">🧠</span>
        <span className="panel-title">LONG-TERM MEMORY</span>
        <span className="memory-count-badge">{records.length} Saved</span>
      </div>

      <div className="memory-controls">
        <input
          type="text"
          className="hud-input memory-search-input"
          placeholder="Search memories & preferences..."
          value={query}
          onChange={handleSearchChange}
        />
        <div className="category-chips">
          {["all", "projects", "preferences", "workflows"].map((cat) => (
            <button
              key={cat}
              className={`cat-chip ${selectedCat === cat ? "active" : ""}`}
              onClick={() => setSelectedCat(cat)}
            >
              {cat.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="memory-records-list">
        {filtered.length === 0 ? (
          <div className="no-memories">No memory records found.</div>
        ) : (
          filtered.map((r) => (
            <div key={r.id} className="memory-card">
              <span className="mem-category">{r.category.toUpperCase()}</span>
              <span className="mem-content">{r.content}</span>
              {onDeleteRecord && (
                <button
                  className="hud-icon-btn mem-del-btn"
                  onClick={() => onDeleteRecord(r.id)}
                  title="Delete memory"
                >
                  ✕
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
