import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("jarvis.context")

class ActiveContext(BaseModel):
    """
    Lightweight Session & Working Context tracking active application, browser state,
    recent search queries, last executed tools, and multi-turn conversation history.
    """
    active_application: str = Field(default="Desktop")
    active_browser_url: str = Field(default="about:blank")
    active_browser_title: str = Field(default="")
    active_browser_domain: str = Field(default="")
    last_search_query: str = Field(default="")
    last_user_command: str = Field(default="")
    last_successful_tool: str = Field(default="")
    last_target_channel: str = Field(default="")
    last_target_app: str = Field(default="")
    last_target_folder: str = Field(default="")
    last_target_file: str = Field(default="")
    last_updated_timestamp: float = Field(default_factory=time.time)
    conversation_turns: List[Dict[str, str]] = Field(default_factory=list)

    def update_browser_state(self, url: str, title: str = ""):
        self.active_browser_url = url
        self.active_browser_title = title
        self.last_updated_timestamp = time.time()
        
        # Parse domain
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            self.active_browser_domain = parsed.netloc or parsed.path.split('/')[0]
        except Exception:
            self.active_browser_domain = url

    def add_turn(self, role: str, content: str):
        self.conversation_turns.append({"role": role, "content": content})
        # Keep last 10 turns for lightweight context window
        if len(self.conversation_turns) > 10:
            self.conversation_turns = self.conversation_turns[-10:]
        self.last_updated_timestamp = time.time()

    def resolve_pronouns(self, text: str) -> str:
        """
        Resolves implicit pronouns ('iska', 'isme', 'usme', 'this', 'that', 'it', 'pehla wala')
        using the active working context.
        """
        t_lower = text.lower()
        
        # Pronoun resolution for YouTube channel / video
        if any(kw in t_lower for kw in ["channel", "popular", "video", "chalao", "play", "most watched"]):
            if not any(pn in t_lower for pn in ["youtube", "google"]) and (self.last_target_channel or "youtube.com" in self.active_browser_url or self.last_search_query):
                ctx_query = self.last_target_channel or self.last_search_query or "hasmob002"
                return f"YouTube on channel '{ctx_query}': {text}"

        # Pronoun resolution for active desktop app ("isme likho")
        if any(kw in t_lower for kw in ["isme", "usme", "in this", "in that"]) and any(kw in t_lower for kw in ["likho", "write", "type", "save"]):
            target_app = self.last_target_app or self.active_application or "Notepad"
            return f"In active application '{target_app}': {text}"

        return text

    def format_context_for_prompt(self) -> str:
        lines = ["[ACTIVE WORKING CONTEXT]"]
        lines.append(f"- Active Application: {self.active_application}")
        lines.append(f"- Active Browser URL: {self.active_browser_url}")
        if self.active_browser_title:
            lines.append(f"- Active Browser Title: {self.active_browser_title}")
        if self.active_browser_domain:
            lines.append(f"- Active Browser Domain: {self.active_browser_domain}")
        if self.last_search_query:
            lines.append(f"- Last Search Query: {self.last_search_query}")
        if self.last_target_channel:
            lines.append(f"- Last Target Channel: {self.last_target_channel}")
        if self.last_target_app:
            lines.append(f"- Last Target App: {self.last_target_app}")
        if self.last_target_folder:
            lines.append(f"- Last Target Folder: {self.last_target_folder}")
        if self.last_successful_tool:
            lines.append(f"- Last Successful Action: {self.last_successful_tool}")
        if self.last_user_command:
            lines.append(f"- Previous User Command: {self.last_user_command}")
        
        return "\n".join(lines)

# Singleton ActiveContext
active_context = ActiveContext()
