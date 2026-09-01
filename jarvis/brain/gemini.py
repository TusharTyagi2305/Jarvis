import json
import logging
from typing import List, Dict, Any, Optional
from jarvis.brain.base import BaseLLMProvider, LLMResponse, ToolCallRequest
from jarvis.brain.mock import MockLLMProvider

logger = logging.getLogger("jarvis.brain.gemini")

class GeminiLLMProvider(BaseLLMProvider):
    """
    LLM Provider integrating Google Gemini API with function calling capabilities.
    Falls back gracefully to MockLLMProvider if GEMINI_API_KEY is not set or API error occurs.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._mock_fallback = MockLLMProvider()

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"LLM PROVIDER: GEMINI | MODEL: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}. Will fallback to Mock provider.")
                self.client = None
        else:
            logger.info("LLM PROVIDER: MOCK (Offline fallback mode)")
            self.client = None

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None
    ) -> LLMResponse:
        if not self.client:
            logger.info("No Gemini API client active; delegating request to MockLLMProvider.")
            return self._mock_fallback.generate(messages, tools, system_instruction)

        try:
            from google.genai import types
            from jarvis.context import active_context

            # Format tool declarations for google-genai SDK
            tool_declarations = []
            if tools:
                func_decls = []
                for tool in tools:
                    func_decls.append(types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool.get("parameters")
                    ))
                tool_declarations = [types.Tool(function_declarations=func_decls)]

            # Prepend Active Working Context to System Instruction
            sys_inst = system_instruction or "You are JARVIS, a personal AI desktop assistant."
            ctx_str = active_context.format_context_for_prompt()
            full_system_instruction = f"{sys_inst}\n\n{ctx_str}"

            config = types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                tools=tool_declarations if tool_declarations else None,
                temperature=0.2
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            tool_calls = []
            response_text = ""

            if response.function_calls:
                for fc in response.function_calls:
                    tool_calls.append(ToolCallRequest(
                        tool_name=fc.name,
                        args=dict(fc.args) if fc.args else {}
                    ))

            if response.text:
                response_text = response.text

            return LLMResponse(
                content=response_text if response_text else None,
                tool_calls=tool_calls
            )

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}. Falling back to MockLLMProvider.")
            return self._mock_fallback.generate(messages, tools, system_instruction)
