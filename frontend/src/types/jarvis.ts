export type AgentState = 
  | "IDLE"
  | "DISABLED"
  | "PERMISSION_REQUIRED"
  | "WAKE_LISTENING"
  | "WAKE_DETECTED"
  | "LISTENING"
  | "TRANSCRIBING"
  | "PROCESSING"
  | "PLANNING"
  | "EXECUTING"
  | "VERIFYING"
  | "WAITING"
  | "PAUSED"
  | "SPEAKING"
  | "COMPLETED"
  | "ERROR";

export type RiskLevel = "SAFE" | "CONFIRM" | "DANGEROUS";

export interface TelemetryData {
  os: string;
  processor?: string;
  cpu_cores?: number;
  cpu_usage_percent: number;
  memory_total_gb: number;
  memory_available_gb: number;
  memory_used_percent: number;
  disk_total_gb: number;
  disk_free_gb: number;
  disk_used_percent: number;
  battery?: {
    percent: number;
    power_plugged: boolean;
    secsleft: number;
  } | null;
}

export interface ActivityItem {
  id: string;
  timestamp: string;
  type: "state" | "command" | "task_started" | "tool_started" | "tool_completed" | "confirmation" | "task_completed" | "error";
  title: string;
  details?: string;
  status: "info" | "pending" | "success" | "warning" | "error";
}

export interface ConfirmationRequest {
  confirmation_id: string;
  tool_name: string;
  risk_level: RiskLevel;
  message: string;
  parameters: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "jarvis";
  text: string;
  timestamp: string;
  pendingConfirmation?: ConfirmationRequest;
}

export interface WSEventMessage {
  type: string;
  state?: AgentState;
  task_id?: string;
  description?: string;
  tool?: string;
  args?: Record<string, any>;
  success?: boolean;
  result?: any;
  error?: string;
  confirmation_id?: string;
  tool_name?: string;
  risk_level?: RiskLevel;
  message?: string;
  parameters?: Record<string, any>;
  cpu?: number;
  ram?: number;
  disk?: number;
  battery?: any;
  os_info?: string;
  voice_state?: AgentState;
  text?: string;
  action?: string;
  target?: string;
  url?: string;
  title?: string;
  tabs?: any[];
  active_window?: string;
  category?: string;
  content?: string;
}
