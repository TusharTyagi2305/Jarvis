import json
from typing import List, Dict, Any, Optional
from jarvis.brain.base import BaseLLMProvider, LLMResponse, ToolCallRequest

class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider used for offline testing, unit tests, and keyless fallback.
    Analyzes request text to simulate function calling and reasoning.
    """

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None
    ) -> LLMResponse:
        if not messages:
            return LLMResponse(content="No request provided.")

        last_msg = messages[-1]
        from jarvis.brain.response_formatter import ResponseFormatter

        # If previous message is a tool response, produce a clean natural summary
        if last_msg.get("role") == "tool":
            content = last_msg.get("content", "")
            tool_name = last_msg.get("name", "")
            user_req = messages[0].get("content", "") if messages else ""
            clean_resp = ResponseFormatter.format_tool_result(tool_name, content, user_req)
            return LLMResponse(
                content=clean_resp,
                tool_calls=[]
            )

        user_text = str(last_msg.get("content", "")).lower()
        if ":" in user_text:
            user_text = user_text.split(":")[-1].strip()

        # 1. System / Hardware Info Parsing
        if "battery" in user_text or "system" in user_text or "ram" in user_text or "cpu" in user_text:
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="get_system_info", args={})]
            )

        # 2. Desktop Application Launch Parsing
        if "notepad" in user_text:
            if "close" in user_text or "band" in user_text:
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="close_application", args={"process_name": "notepad.exe"})]
                )
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="open_application", args={"app_name": "notepad"})]
            )
        elif any(kw in user_text for kw in ["open", "kholo", "launch"]) and any(app in user_text for app in ["calc", "calculator", "chrome", "vscode", "code"]):
            app = "chrome" if "chrome" in user_text else ("calc" if "calc" in user_text or "calculator" in user_text else "vscode")
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="open_application", args={"app_name": app})]
            )

        # 3. Contextual Follow-Ups (Channel, Video, Play)
        if "channel" in user_text:
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="browser_click", args={"target": "channel"})]
            )
        elif any(kw in user_text for kw in ["popular", "most watched"]):
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="browser_click", args={"target": "most watched video"})]
            )

        # 4. Web / Browser Intent Parsing
        if any(term in user_text for term in ["youtube", "google", "bing", "website", "web", "internet", "browser", "url", "search", "dhundho", "dhoondho", "dikhao", "hasmob002"]):
            if "youtube" in user_text or "hasmob002" in user_text or "search" in user_text or "dhundho" in user_text:
                if any(kw in user_text for kw in ["search", "dhundho", "dhoondho", "dikhao", "find", "karo", "hasmob002"]):
                    parts = user_text.replace("dhundho", "search").replace("dhoondho", "search").replace("dikhao", "search").split("search")
                    query = parts[-1].replace("for", "").replace("par", "").replace("pe", "").replace("ko", "").replace("youtube", "").replace("karo", "").strip() or "hasmob002"
                    return LLMResponse(
                        tool_calls=[ToolCallRequest(tool_name="browser_search", args={"query": query, "engine": "youtube"})]
                    )
                else:
                    return LLMResponse(
                        tool_calls=[ToolCallRequest(tool_name="browser_navigate", args={"url": "https://www.youtube.com"})]
                    )
            elif "google" in user_text:
                if any(kw in user_text for kw in ["search", "dhundho", "dhoondho"]):
                    parts = user_text.replace("dhundho", "search").split("search")
                    query = parts[-1].replace("for", "").replace("par", "").replace("pe", "").strip() or "search query"
                    return LLMResponse(
                        tool_calls=[ToolCallRequest(tool_name="browser_search", args={"query": query, "engine": "google"})]
                    )
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="browser_navigate", args={"url": "https://www.google.com"})]
                )
            elif any(kw in user_text for kw in ["search", "dhundho", "dhoondho"]):
                parts = user_text.replace("dhundho", "search").split("search")
                query = parts[-1].replace("for", "").replace("online", "").replace("the web", "").strip() or "query"
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="browser_search", args={"query": query})]
                )

        # 5. Screen Vision Intent Parsing
        if "screen" in user_text or "button" in user_text:
            if "inspect" in user_text or "analyze" in user_text:
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="screen_analyze", args={"prompt": user_text})]
                )
            elif "find" in user_text or "element" in user_text or "button" in user_text:
                target = "Run button"
                if "button" in user_text:
                    idx = user_text.find("button")
                    words = user_text[:idx+6].split()
                    target = " ".join(words[-2:]) if len(words) >= 2 else "Run button"
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="screen_find_element", args={"target": target.title()})]
                )
            elif "screenshot" in user_text:
                return LLMResponse(
                    tool_calls=[ToolCallRequest(tool_name="take_screenshot", args={})]
                )

        # 6. Memory Intent Parsing
        if "remember" in user_text or "memory" in user_text or ("what is my" in user_text and "project" in user_text) or "mera main project" in user_text:
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="memory_search", args={"query": user_text})]
            )

        # 7. File Operations / Writing Parsing
        if any(kw in user_text for kw in ["likho", "write", "type"]):
            return LLMResponse(
                tool_calls=[ToolCallRequest(tool_name="open_application", args={"app_name": "notepad"})]
            )

        # Contextual relevant response (NO generic reset greeting)
        return LLMResponse(
            content=f"Processing request: '{user_text}'. All relevant tools evaluated.",
            tool_calls=[]
        )
