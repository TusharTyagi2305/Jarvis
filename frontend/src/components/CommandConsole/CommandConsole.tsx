import React, { useState, useEffect, useRef } from "react";
import type { AgentState } from "../../types/jarvis";
import "./CommandConsole.css";

interface CommandConsoleProps {
  onSendCommand: (command: string) => void;
  disabled?: boolean;
  agentState?: AgentState;
  onMicStateChange?: (state: AgentState) => void;
  onMicPermissionError?: (error: string) => void;
}

export const CommandConsole: React.FC<CommandConsoleProps> = ({
  onSendCommand,
  disabled,
  agentState = "IDLE",
  onMicStateChange,
  onMicPermissionError,
}) => {
  const [input, setInput] = useState<string>("");
  const [micState, setMicState] = useState<AgentState>(agentState);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const recognitionRef = useRef<any>(null);
  const isTtsSpeakingRef = useRef<boolean>(false);
  const wakeWordTimeoutRef = useRef<any>(null);

  // Sync state changes from props
  useEffect(() => {
    setMicState(agentState);
  }, [agentState]);

  // Request microphone permission on mount
  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(() => {
          setPermissionGranted(true);
          startWakeWordListener();
        })
        .catch((err) => {
          console.warn("Microphone permission denied:", err);
          setPermissionGranted(false);
          setMicState("PERMISSION_REQUIRED");
          onMicStateChange?.("PERMISSION_REQUIRED");
          onMicPermissionError?.("Microphone permission required for hands-free wake word detection.");
        });
    } else {
      setPermissionGranted(false);
      setMicState("PERMISSION_REQUIRED");
    }

    return () => {
      stopListener();
    };
  }, []);

  const stopListener = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
    if (wakeWordTimeoutRef.current) {
      clearTimeout(wakeWordTimeoutRef.current);
    }
  };

  const startWakeWordListener = () => {
    if (isTtsSpeakingRef.current) return;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatusMessage("Web Speech API unsupported");
      return;
    }

    stopListener();

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-IN";
      recognition.interimResults = true;
      recognition.continuous = true;

      recognition.onstart = () => {
        setMicState("WAKE_LISTENING");
        onMicStateChange?.("WAKE_LISTENING");
        setStatusMessage("WAKE LISTENING");
      };

      recognition.onresult = (event: any) => {
        if (isTtsSpeakingRef.current) return;

        const results = event.results;
        for (let i = event.resultIndex; i < results.length; i++) {
          const transcript = results[i][0].transcript.trim().toLowerCase();

          // Detect wake word variations
          if (
            transcript.includes("jarvis") ||
            transcript.includes("hey jarvis") ||
            transcript.includes("ok jarvis")
          ) {
            handleWakeWordDetected();
            break;
          }
        }
      };

      recognition.onerror = (err: any) => {
        if (err.error === "not-allowed") {
          setPermissionGranted(false);
          setMicState("PERMISSION_REQUIRED");
          onMicStateChange?.("PERMISSION_REQUIRED");
          onMicPermissionError?.("Microphone permission denied.");
        } else if (err.error !== "no-speech") {
          console.warn("Wake word listener error:", err.error);
        }
      };

      recognition.onend = () => {
        // Auto-restart wake listener if still in WAKE_LISTENING mode and TTS not speaking
        if (!isTtsSpeakingRef.current && permissionGranted !== false) {
          setTimeout(() => startWakeWordListener(), 300);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      console.error("Failed to start speech recognition:", e);
    }
  };

  const handleWakeWordDetected = () => {
    stopListener();

    setMicState("WAKE_DETECTED");
    onMicStateChange?.("WAKE_DETECTED");
    setStatusMessage("WAKE DETECTED");

    // Speak "Yes, sir?" with mic paused during TTS
    isTtsSpeakingRef.current = true;
    setMicState("SPEAKING");

    if (window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance("Yes, sir?");
        utterance.lang = "en-IN";
        utterance.onend = () => {
          isTtsSpeakingRef.current = false;
          startCommandListening();
        };
        utterance.onerror = () => {
          isTtsSpeakingRef.current = false;
          startCommandListening();
        };
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        isTtsSpeakingRef.current = false;
        startCommandListening();
      }
    } else {
      isTtsSpeakingRef.current = false;
      startCommandListening();
    }
  };

  const startCommandListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    setMicState("LISTENING");
    onMicStateChange?.("LISTENING");
    setStatusMessage("LISTENING FOR COMMAND...");

    try {
      const commandRecognition = new SpeechRecognition();
      commandRecognition.lang = "en-IN";
      commandRecognition.interimResults = true;
      commandRecognition.continuous = false;

      // Set conversation timeout (8s)
      wakeWordTimeoutRef.current = setTimeout(() => {
        try {
          commandRecognition.stop();
        } catch (e) {}
        startWakeWordListener();
      }, 8000);

      commandRecognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript.trim();
        setInput(transcript);

        if (event.results[0].isFinal) {
          clearTimeout(wakeWordTimeoutRef.current);
          commandRecognition.stop();
          if (transcript) {
            onSendCommand(transcript);
            setInput("");
          }
          startWakeWordListener();
        }
      };

      commandRecognition.onend = () => {
        clearTimeout(wakeWordTimeoutRef.current);
        startWakeWordListener();
      };

      commandRecognition.onerror = () => {
        clearTimeout(wakeWordTimeoutRef.current);
        startWakeWordListener();
      };

      commandRecognition.start();
    } catch (e) {
      startWakeWordListener();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendCommand(input.trim());
    setInput("");
  };

  const toggleMic = () => {
    if (disabled) return;
    if (permissionGranted === false) {
      // Re-request permission
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(() => {
          setPermissionGranted(true);
          startWakeWordListener();
        })
        .catch(() => {
          onMicPermissionError?.("Microphone permission denied by browser settings.");
        });
      return;
    }

    if (micState === "LISTENING" || micState === "WAKE_LISTENING") {
      stopListener();
      setMicState("IDLE");
      setStatusMessage("MIC PAUSED");
    } else {
      startWakeWordListener();
    }
  };

  const getBadgeClass = () => {
    switch (micState) {
      case "WAKE_LISTENING":
        return "badge-listening";
      case "WAKE_DETECTED":
      case "SPEAKING":
        return "badge-speaking";
      case "LISTENING":
      case "TRANSCRIBING":
        return "badge-active";
      case "PROCESSING":
      case "PLANNING":
      case "EXECUTING":
        return "badge-processing";
      case "PERMISSION_REQUIRED":
      case "ERROR":
        return "badge-error";
      default:
        return "badge-idle";
    }
  };

  const getStatusLabel = () => {
    if (permissionGranted === false || micState === "PERMISSION_REQUIRED") {
      return "PERMISSION REQUIRED";
    }
    switch (micState) {
      case "WAKE_LISTENING":
        return "WAKE LISTENING";
      case "WAKE_DETECTED":
        return "WAKE DETECTED";
      case "LISTENING":
        return "LISTENING";
      case "TRANSCRIBING":
        return "TRANSCRIBING";
      case "PROCESSING":
        return "PROCESSING";
      case "SPEAKING":
        return "SPEAKING";
      case "ERROR":
        return "MICROPHONE ERROR";
      default:
        return statusMessage || "READY";
    }
  };

  return (
    <div className="command-console-wrapper">
      <form className="command-console hud-panel" onSubmit={handleSubmit}>
        <div className="input-prefix">❯</div>
        <input
          type="text"
          className="hud-input"
          placeholder={
            micState === "LISTENING"
              ? "Listening to your voice command..."
              : "Ask JARVIS... (e.g. 'Open YouTube and search hasmob002', 'Open Notepad')"
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled}
        />
        <div className="console-actions">
          <span className={`voice-status-badge ${getBadgeClass()}`}>
            ● {getStatusLabel()}
          </span>
          <button
            type="button"
            className={`hud-icon-btn mic-btn ${
              micState === "WAKE_LISTENING" || micState === "LISTENING" ? "listening" : ""
            } ${micState === "PERMISSION_REQUIRED" ? "permission-alert" : ""}`}
            onClick={toggleMic}
            title={
              permissionGranted === false
                ? "Microphone permission required! Click to allow access"
                : "Toggle Voice Wake Word Listener"
            }
            disabled={disabled}
          >
            {micState === "PERMISSION_REQUIRED" ? "⚠️" : micState === "WAKE_LISTENING" ? "🎙" : "🔴"}
          </button>
          <button
            type="submit"
            className="hud-btn submit-btn"
            disabled={disabled || !input.trim() || micState === "SPEAKING"}
          >
            SEND
          </button>
        </div>
      </form>
      {permissionGranted === false && (
        <div className="mic-permission-banner">
          ⚠️ MICROPHONE PERMISSION REQUIRED: Please click the mic icon or allow microphone access in your browser location bar to enable hands-free "Jarvis" wake word.
        </div>
      )}
    </div>
  );
};
