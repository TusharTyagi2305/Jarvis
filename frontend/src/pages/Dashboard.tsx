import React, { useState, useCallback } from "react";
import { Header } from "../components/Header/Header";
import { JarvisCore } from "../components/JarvisCore/JarvisCore";
import { SystemTelemetry } from "../components/SystemTelemetry/SystemTelemetry";
import { ActivityFeed } from "../components/ActivityFeed/ActivityFeed";
import { ChatPanel } from "../components/ChatPanel/ChatPanel";
import { CommandConsole } from "../components/CommandConsole/CommandConsole";
import { BrowserPanel } from "../components/BrowserPanel/BrowserPanel";
import { ScreenVisionPanel } from "../components/ScreenVisionPanel/ScreenVisionPanel";
import type { VisionElementInfo } from "../components/ScreenVisionPanel/ScreenVisionPanel";
import { MemoryPanel } from "../components/MemoryPanel/MemoryPanel";
import type { MemoryRecordInfo } from "../components/MemoryPanel/MemoryPanel";
import { TaskExecutionPanel } from "../components/TaskExecutionPanel/TaskExecutionPanel";
import type { TaskStepInfo } from "../components/TaskExecutionPanel/TaskExecutionPanel";
import { SystemHealthPanel } from "../components/SystemHealthPanel/SystemHealthPanel";
import { ConfirmationModal } from "../components/ConfirmationModal/ConfirmationModal";
import { SettingsModal } from "../components/SettingsModal/SettingsModal";

import { useWebSocket } from "../hooks/useWebSocket";
import { useTelemetry } from "../hooks/useTelemetry";
import { sendCommand, confirmAction } from "../services/api";
import type { AgentState, ActivityItem, ChatMessage, ConfirmationRequest, WSEventMessage } from "../types/jarvis";
import "./Dashboard.css";

export const Dashboard: React.FC = () => {
  const [agentState, setAgentState] = useState<AgentState>("IDLE");
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [pendingConfirmation, setPendingConfirmation] = useState<ConfirmationRequest | null>(null);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Task Graph state
  const [taskGoal, setTaskGoal] = useState<string>("Inspect & verify project workspace");
  const [taskStatus, setTaskStatus] = useState<string>("IDLE");
  const [taskSteps, setTaskSteps] = useState<TaskStepInfo[]>([]);

  // Browser state
  const [browserTitle, setBrowserTitle] = useState<string>("Ready");
  const [browserUrl, setBrowserUrl] = useState<string>("https://www.google.com");
  const [browserAction, setBrowserAction] = useState<string>("Idle");
  const [browserTabs, setBrowserTabs] = useState<any[]>([]);
  const [isBrowserActive, setIsBrowserActive] = useState<boolean>(false);

  // Vision state
  const [visionStatus, setVisionStatus] = useState<string>("IDLE");
  const [visionWindow, setVisionWindow] = useState<string>("Windows Desktop");
  const [visionDescription, setVisionDescription] = useState<string>("No active visual analysis.");
  const [visionElements, setVisionElements] = useState<VisionElementInfo[]>([]);

  // Memory state
  const [memoryRecords, setMemoryRecords] = useState<MemoryRecordInfo[]>([
    { id: "1", category: "projects", content: "Main project: LearnGen AI" },
    { id: "2", category: "preferences", content: "Preferred browser: Chrome" }
  ]);

  const { telemetry } = useTelemetry(4000);

  const addActivity = useCallback((type: ActivityItem["type"], title: string, details?: string, status: ActivityItem["status"] = "info") => {
    const newItem: ActivityItem = {
      id: `act_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type,
      title,
      details,
      status,
    };
    setActivities((prev) => [...prev.slice(-49), newItem]);
  }, []);

  const handleWSMessage = useCallback((event: WSEventMessage) => {
    switch (event.type) {
      case "state":
        if (event.state) setAgentState(event.state);
        break;

      case "voice_state":
        if (event.voice_state) setAgentState(event.voice_state);
        break;

      case "transcript":
        if (event.text) {
          addActivity("command", `Voice Transcript: ${event.text}`, undefined, "info");
        }
        break;

      case "speech_started":
        setAgentState("SPEAKING");
        break;

      case "speech_completed":
        setAgentState("IDLE");
        break;

      case "browser_action":
        setIsBrowserActive(true);
        if (event.action && event.target) {
          setBrowserAction(`${event.action.toUpperCase()}: ${event.target}`);
          addActivity("tool_started", `Browser Action: ${event.action}`, event.target, "pending");
        }
        break;

      case "browser_page_changed":
        setIsBrowserActive(true);
        if (event.title) setBrowserTitle(event.title);
        if (event.url) setBrowserUrl(event.url);
        if (event.tabs) setBrowserTabs(event.tabs);
        setBrowserAction("Page Loaded");
        break;

      case "screen_analysis_started":
        setVisionStatus("ANALYZING");
        break;

      case "screen_analysis_completed":
        setVisionStatus("COMPLETED");
        if (event.description) setVisionDescription(event.description);
        if (event.active_window) setVisionWindow(event.active_window);
        addActivity("command", "Screen Vision Analysis Complete", event.description, "success");
        break;

      case "screen_element_found":
        setVisionStatus("ELEMENT_FOUND");
        if (event.text) {
          setVisionElements((prev) => [
            {
              type: event.tool_name || "element",
              text: event.text || "",
              x: event.cpu || 0,
              y: event.ram || 0,
              confidence: event.disk || 0.9,
            },
            ...prev.slice(0, 4)
          ]);
        }
        break;

      case "screen_action":
        setVisionStatus("ACTING");
        break;

      case "screen_verification_started":
        setVisionStatus("VERIFYING");
        break;

      case "screen_verification_completed":
        setVisionStatus("COMPLETED");
        break;

      case "memory_saved":
        if (event.content) {
          const newContent = event.content;
          setMemoryRecords((prev) => [
            { id: `mem_${Date.now()}`, category: event.category || "general", content: newContent },
            ...prev
          ]);
          addActivity("command", `Memory Saved: [${event.category}]`, newContent, "success");
        }
        break;

      case "memory_deleted":
        setMemoryRecords((prev) => prev.filter((m) => m.id !== event.action && m.content !== event.action));
        addActivity("command", "Memory Record Deleted", event.action, "info");
        break;

      case "memory_blocked":
        addActivity("error", "Sensitive Memory Storage Blocked", event.description || "Sensitive credentials filtered.", "warning");
        break;

      case "task_plan_created":
        if (event.text) setTaskGoal(event.text);
        setTaskStatus("EXECUTING");
        addActivity("task_started", "Multi-Step Task Plan Created", event.text, "pending");
        break;

      case "task_step_started":
        if (event.target) {
          setTaskSteps((prev) => {
            const exists = prev.find((s) => s.id === event.target);
            if (exists) {
              return prev.map((s) => (s.id === event.target ? { ...s, status: "RUNNING" } : s));
            }
            return [...prev, { id: event.target || `step_${Date.now()}`, description: event.action || "Executing step", status: "RUNNING", tool: event.tool_name }];
          });
        }
        break;

      case "task_step_completed":
        if (event.target) {
          setTaskSteps((prev) => prev.map((s) => (s.id === event.target ? { ...s, status: "COMPLETED" } : s)));
        }
        break;

      case "task_step_failed":
        if (event.target) {
          setTaskSteps((prev) => prev.map((s) => (s.id === event.target ? { ...s, status: "FAILED", error: event.description } : s)));
        }
        break;

      case "task_paused":
        setTaskStatus("PAUSED");
        addActivity("state", "Task Execution Paused", "", "info");
        break;

      case "task_resumed":
        setTaskStatus("EXECUTING");
        addActivity("state", "Task Execution Resumed", "", "info");
        break;

      case "task_cancelled":
        setTaskStatus("CANCELLED");
        addActivity("state", "Task Execution Cancelled", "", "warning");
        break;

      case "task_started":
        addActivity("task_started", "Command Received", event.description, "pending");
        break;

      case "tool_started":
        if (event.tool) {
          addActivity("tool_started", `Executing Tool: ${event.tool}`, JSON.stringify(event.args || {}), "pending");
        }
        break;

      case "tool_completed":
        if (event.tool) {
          addActivity(
            "tool_completed",
            `Tool Output: ${event.tool}`,
            event.success ? JSON.stringify(event.result || "Success") : `Error: ${event.error}`,
            event.success ? "success" : "error"
          );
        }
        break;

      case "confirmation_required":
        if (event.confirmation_id && event.tool_name) {
          const req: ConfirmationRequest = {
            confirmation_id: event.confirmation_id,
            tool_name: event.tool_name,
            risk_level: event.risk_level || "CONFIRM",
            message: event.message || `Confirm execution of ${event.tool_name}`,
            parameters: event.parameters || {},
          };
          setPendingConfirmation(req);
          addActivity("confirmation", `Permission Required: ${event.tool_name}`, req.message, "warning");
        }
        break;

      case "task_completed":
        addActivity("task_completed", "Task Complete", event.result, event.success ? "success" : "error");
        if (event.result) {
          setChatMessages((prev) => [
            ...prev,
            {
              id: `msg_${Date.now()}`,
              sender: "jarvis",
              text: event.result,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
          ]);
        }
        setIsProcessing(false);
        break;

      case "error":
        addActivity("error", "Error Occurred", event.error || event.message, "error");
        setIsProcessing(false);
        break;

      default:
        break;
    }
  }, [addActivity]);

  const { isConnected } = useWebSocket(handleWSMessage);

  const handleUserCommand = async (cmdText: string) => {
    setIsProcessing(true);
    setAgentState("PROCESSING");

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setChatMessages((prev) => [
      ...prev,
      { id: `msg_${Date.now()}`, sender: "user", text: cmdText, timestamp: time },
    ]);

    addActivity("command", `User: ${cmdText}`, undefined, "info");

    try {
      const apiRes = await sendCommand(cmdText);
      if (apiRes.response && apiRes.response.pending_confirmation) {
        const conf = apiRes.response.pending_confirmation;
        setPendingConfirmation({
          confirmation_id: conf.token,
          tool_name: conf.tool_name,
          risk_level: conf.risk_level,
          message: conf.reason,
          parameters: conf.tool_args,
        });
      }
    } catch (err: any) {
      addActivity("error", "Command submission failed", err.message, "error");
      setAgentState("ERROR");
      setIsProcessing(false);
    }
  };

  const handleConfirmAction = async (token: string) => {
    setPendingConfirmation(null);
    setAgentState("PROCESSING");
    addActivity("confirmation", "User Approved Action Token", token, "info");

    try {
      const lastUserMsg = [...chatMessages].reverse().find((m) => m.sender === "user")?.text || "Confirmed Action";
      const apiRes = await confirmAction(token, lastUserMsg);
      if (apiRes.final_response) {
        setChatMessages((prev) => [
          ...prev,
          {
            id: `msg_${Date.now()}`,
            sender: "jarvis",
            text: apiRes.final_response,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
      setAgentState("COMPLETED");
    } catch (err: any) {
      addActivity("error", "Confirmation submission failed", err.message, "error");
      setAgentState("ERROR");
    } finally {
      setIsProcessing(false);
    }
  };

  const [isVoiceReady, setIsVoiceReady] = useState<boolean>(true);
  const [isMinimalMode, setIsMinimalMode] = useState<boolean>(false);
  const [isAlwaysOnTop, setIsAlwaysOnTop] = useState<boolean>(false);

  const handleToggleAlwaysOnTop = () => {
    const nextVal = !isAlwaysOnTop;
    setIsAlwaysOnTop(nextVal);
    if ((window as any).pywebview && (window as any).pywebview.api) {
      (window as any).pywebview.api.toggle_always_on_top(nextVal);
    }
  };

  return (
    <div className={`dashboard-container ${isMinimalMode ? "minimal-hud-mode" : ""}`}>
      {/* HUD Header */}
      <Header
        isConnected={isConnected}
        onOpenSettings={() => setShowSettings(true)}
        isMinimalMode={isMinimalMode}
        onToggleMinimalMode={() => setIsMinimalMode((prev) => !prev)}
        isAlwaysOnTop={isAlwaysOnTop}
        onToggleAlwaysOnTop={handleToggleAlwaysOnTop}
      />

      {/* Main Content Layout */}
      <div className="dashboard-grid">
        {/* Top Center: JARVIS Core & Search/Command Input */}
        <div className="core-section hud-panel">
          <JarvisCore state={agentState} />
          <CommandConsole
            onSendCommand={handleUserCommand}
            disabled={isProcessing}
            agentState={agentState}
            onMicStateChange={(st) => setAgentState(st)}
            onMicPermissionError={() => setIsVoiceReady(false)}
          />
        </div>

        {/* Middle Left: Telemetry & Browser Panels */}
        <div className="telemetry-section" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <SystemHealthPanel
            health={{
              core: true,
              voice: isVoiceReady,
              vision: true,
              browser: true,
              memory: true,
              llm: true,
            }}
          />
          <SystemTelemetry telemetry={telemetry} />
          <BrowserPanel
            isConnected={isConnected || isBrowserActive}
            pageTitle={browserTitle}
            currentUrl={browserUrl}
            currentAction={browserAction}
            tabs={browserTabs}
          />
          <ScreenVisionPanel
            status={visionStatus}
            activeWindow={visionWindow}
            description={visionDescription}
            elements={visionElements}
          />
          <MemoryPanel
            records={memoryRecords}
            onDeleteRecord={(id) => {
              setMemoryRecords((prev) => prev.filter((m) => m.id !== id));
            }}
          />
          <TaskExecutionPanel
            goal={taskGoal}
            status={taskStatus}
            steps={taskSteps}
            onPause={async () => {
              try {
                await fetch('/api/task/pause', { method: 'POST' });
                setTaskStatus('PAUSED');
              } catch (e) {}
            }}
            onResume={async () => {
              try {
                await fetch('/api/task/resume', { method: 'POST' });
                setTaskStatus('EXECUTING');
              } catch (e) {}
            }}
            onCancel={async () => {
              try {
                await fetch('/api/task/cancel', { method: 'POST' });
                setTaskStatus('CANCELLED');
              } catch (e) {}
            }}
          />
        </div>

        {/* Middle Center: Conversation Stream */}
        <div className="chat-section">
          <ChatPanel
            messages={chatMessages}
            onConfirmToken={(token) => {
              handleConfirmAction(token);
            }}
          />
        </div>

        {/* Middle Right: Task Activity Feed */}
        <div className="activity-section">
          <ActivityFeed activities={activities} />
        </div>
      </div>



      {/* Confirmation Dialog Overlay */}
      {pendingConfirmation && (
        <ConfirmationModal
          request={pendingConfirmation}
          onConfirm={handleConfirmAction}
          onCancel={() => setPendingConfirmation(null)}
        />
      )}

      {/* Settings Modal Overlay */}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
};
