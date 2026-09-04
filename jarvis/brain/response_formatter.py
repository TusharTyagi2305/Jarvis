import re
import json
import logging
from typing import Any, Dict, Optional, Union

from jarvis.config import settings

logger = logging.getLogger("jarvis.brain.response_formatter")

PROPER_NOUNS = [
    "YouTube", "Chrome", "VS Code", "VSCode", "GitHub", "Notepad", 
    "LearnGen AI", "Hasmob002", "Google", "Bing", "Calculator", 
    "Python", "Windows", "Desktop"
]

HINGLISH_KEYWORDS = [
    "kholo", "khol", "chalao", "dhundho", "dhoondho", "karo", "batao", 
    "dikhao", "likho", "hai", "ka", "ki", "ke", "ko", "par", "pe", 
    "mein", "usme", "isme", "chahiye", "kaunsa", "sabse", "pehla", 
    "baad", "namaste", "shukriya", "bilkul", "ho gaya", "mera", "mere", 
    "meri", "apna", "rakh", "bana", "chala", "bata"
]

class ResponseFormatter:
    """
    Dedicated Natural Response Boundary & Sanitizer.
    Converts raw tool execution data, dictionaries, JSON, and internal system logs
    into concise, natural, human 1-sentence Hindi/Hinglish/English responses.
    """

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detects whether the input text is primarily Hindi (Devanagari/Hinglish) or English.
        """
        if not text:
            return settings.jarvis_language

        # 1. Check for Devanagari script range
        if re.search(r'[\u0900-\u097F]', text):
            return "hi-IN"

        # 2. Check for Hinglish keywords
        words = re.findall(r'\b\w+\b', text.lower())
        hinglish_count = sum(1 for w in words if w in HINGLISH_KEYWORDS)

        if hinglish_count > 0:
            return "hi-IN"

        # Default fallback
        return settings.jarvis_secondary_language if settings.jarvis_secondary_language else "en-IN"

    @staticmethod
    def format_wake_response(user_request: Optional[str] = None) -> str:
        """
        Returns a short polite wake-word response.
        """
        lang = ResponseFormatter.detect_language(user_request) if user_request else settings.jarvis_language
        if "hi" in lang.lower():
            return "Ji sir?"
        return "Yes, sir?"

    @staticmethod
    def sanitize_raw_text(text: str) -> str:
        """
        Removes raw Python dict representations, JSON structures, HTTP status codes,
        tracebacks, and debug wrappers from output strings.
        """
        if not text:
            return ""

        # Remove "Task action complete. Output summary: ..." wrapper
        text = re.sub(r'Task action complete\.\s*Output summary:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'browser_navigate executed successfully with status code \d+\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'browser_search completed with query=[\'"].*?[\'"]\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Task completed after \d+ iterations\.?', '', text, flags=re.IGNORECASE)

        # Remove raw dict/JSON representation if entire string looks like a dict/JSON
        trimmed = text.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
            try:
                data = json.loads(trimmed.replace("'", '"').replace("True", "true").replace("False", "false"))
                return ResponseFormatter.format_tool_result("action", data, "")
            except Exception:
                pass

        # Strip python exceptions / stack trace lines
        if "Traceback (most recent call last)" in text or "Exception:" in text or "Error:" in text:
            return "Main is action ko complete nahi kar paaya."

        return text.strip()

    @staticmethod
    def format_tool_result(
        tool_name: str,
        result_data: Any,
        user_request: str = "",
        is_success: bool = True
    ) -> str:
        """
        Translates raw tool result dictionaries into concise 1-sentence natural responses.
        """
        lang = ResponseFormatter.detect_language(user_request)
        is_hindi = "hi" in lang.lower()

        if not is_success:
            if is_hindi:
                return "Main is action ko complete nahi kar paaya."
            return "I couldn't complete that action, sir."

        req_lower = user_request.lower()

        # Handle dict result extraction
        data = result_data if isinstance(result_data, dict) else {}
        if isinstance(result_data, str) and (result_data.startswith("{") or result_data.startswith("[")):
            try:
                data = json.loads(result_data.replace("'", '"').replace("True", "true").replace("False", "false"))
            except Exception:
                pass

        # 1. System / Battery Info
        if tool_name == "get_system_info" or "battery" in req_lower:
            battery_val = data.get("battery_percent") or data.get("battery")
            if isinstance(battery_val, dict):
                battery_percent = battery_val.get("percent")
            else:
                battery_percent = battery_val

            if battery_percent is not None:
                if is_hindi:
                    return f"Battery {battery_percent} percent hai."
                return f"Your battery is at {battery_percent} percent."
            cpu = data.get("cpu_usage_percent")
            if cpu is not None:
                if is_hindi:
                    return f"System CPU usage {cpu}% hai."
                return f"System CPU usage is at {cpu}%."
            if is_hindi:
                return "System info mil gayi hai."
            return "System status retrieved."

        # 2. Browser Navigation / Search / Click
        if tool_name.startswith("browser_") or any(kw in req_lower for kw in ["youtube", "google", "browser", "website"]):
            query = data.get("query") or data.get("search_query")
            url = data.get("url", "")
            target = str(data.get("target", "")).lower()

            if "youtube" in req_lower or "youtube" in url or "channel" in target or "video" in target:
                if "popular" in req_lower or "video" in req_lower or "chala" in req_lower or "most watched" in target or "popular" in target:
                    return "Popular video चला दिया." if is_hindi else "Playing popular video."
                elif "channel" in req_lower or "channel" in target:
                    return "Channel खोल दिया." if is_hindi else "Channel opened."
                elif "search" in req_lower or query:
                    q_str = query or "search"
                    return f"{q_str} ke results mil gaye." if is_hindi else f"Found results for {q_str}."
                else:
                    return "YouTube खोल दिया." if is_hindi else "Opened YouTube."
            elif "google" in req_lower or "google" in url:
                if "search" in req_lower or query:
                    q_str = query or "search"
                    return f"{q_str} ke results Google par mil gaye." if is_hindi else f"Found results for {q_str}."
                return "Google खोल दिया." if is_hindi else "Opened Google."
            else:
                if query:
                    return f"{query} ke results mil gaye." if is_hindi else f"Found search results for {query}."
                return "Website खोल दी है." if is_hindi else "Navigated to website."

        # 3. Application Launch / Close
        if tool_name in ["open_application", "close_application"] or any(app in req_lower for app in ["notepad", "chrome", "calc", "vscode"]):
            app = data.get("app_name") or data.get("process_name") or "Application"
            app_clean = app.replace(".exe", "").title()
            if tool_name == "close_application" or "close" in req_lower:
                return f"{app_clean} band kar diya." if is_hindi else f"Closed {app_clean}."
            return f"{app_clean} खोल दिया." if is_hindi else f"Opened {app_clean}."

        # 4. Text Writing / Notepad Action
        if "likho" in req_lower or "write" in req_lower or tool_name == "desktop_type":
            return "Likh diya." if is_hindi else "Written to document."

        # 5. File / Folder Operations
        if tool_name in ["create_file", "write_file", "create_folder"]:
            if "folder" in req_lower or tool_name == "create_folder":
                return "Folder bana diya." if is_hindi else "Created folder."
            return "File बना दी hai." if is_hindi else "Created file."
        elif tool_name == "search_files":
            return "Files mil gayi hain." if is_hindi else "Found matching files."

        # 6. Memory Search
        if tool_name == "memory_search" or "remember" in req_lower or "memory" in req_lower:
            return "Memory check kar li hai." if is_hindi else "Memory retrieved."

        # Generic concise fallback
        if is_hindi:
            return "Ho gaya."
        return "Task completed."

    @staticmethod
    def format_final_response(
        raw_response: str,
        user_request: str = "",
        tool_results: Optional[list] = None
    ) -> str:
        """
        Sanitizes and formats the final user-facing response before TTS and UI stream display.
        """
        sanitized = ResponseFormatter.sanitize_raw_text(raw_response)

        # If sanitized text is empty or still contains raw dict string
        if not sanitized or (sanitized.startswith("{") and sanitized.endswith("}")):
            if tool_results and len(tool_results) > 0:
                last_tool = tool_results[-1]
                t_name = last_tool.get("name", "action")
                t_res = last_tool.get("data", {})
                return ResponseFormatter.format_tool_result(t_name, t_res, user_request)
            else:
                lang = ResponseFormatter.detect_language(user_request)
                return "Ho gaya." if "hi" in lang.lower() else "Done."

        # Ensure response ends with clean punctuation and has proper capitalization
        sanitized = sanitized.strip()
        return sanitized
