

from typing import Any, Dict, Iterable, List, Optional, Sequence


class LLMService:
    def __init__(
        self,
        model_name: str,
        api_key: str = "",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        use_chat: bool = True,
        **kwargs: Any,
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.use_chat = use_chat
        self.kwargs = kwargs
        self.client = self._init_client()

    def _init_client(self):
        # Try modern langchain_ollama first, fall back to langchain_community.
        if self.use_chat:
            try:
                from langchain_ollama import ChatOllama

                return ChatOllama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    **self.kwargs,
                )
            except ImportError:
                try:
                    from langchain_community.chat_models import ChatOllama

                    return ChatOllama(
                        model=self.model_name,
                        base_url=self.base_url,
                        temperature=self.temperature,
                        **self.kwargs,
                    )
                except ImportError as exc:
                    raise ImportError(
                        "ChatOllama not available. Install `langchain-ollama` "
                        "or `langchain-community`."
                    ) from exc
        else:
            try:
                from langchain_ollama import Ollama

                return Ollama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    **self.kwargs,
                )
            except ImportError:
                try:
                    from langchain_community.llms import Ollama

                    return Ollama(
                        model=self.model_name,
                        base_url=self.base_url,
                        temperature=self.temperature,
                        **self.kwargs,
                    )
                except ImportError as exc:
                    raise ImportError(
                        "Ollama not available. Install `langchain-ollama` "
                        "or `langchain-community`."
                    ) from exc

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        result = self.client.invoke(prompt, **kwargs)
        # Chat models may return AIMessage; normalize to string
        return getattr(result, "content", result)

    def stream(self, prompt: str, **kwargs: Any) -> Iterable[str]:
        for chunk in self.client.stream(prompt, **kwargs):
            yield getattr(chunk, "content", chunk)

    def get_client(self):
        return self.client

    def get_tool_defs(self, tool_names: Optional[Sequence[str]] = None) -> List[Dict]:
        """
        Return OpenAI-style tool schemas from function_calling.
        If tool_names is None, all available tools are returned.
        """
        try:
            from function_calling import AVAILABLE_TOOLS, get_tools
        except Exception as exc:
            raise ImportError(
                "Unable to load tools from function_calling. "
                "Check function_calling/__init__.py imports."
            ) from exc

        if tool_names:
            return get_tools(list(tool_names))
        return list(AVAILABLE_TOOLS.values())

    def bind_tools(self, tool_names: Optional[Sequence[str]] = None):
        """
        Bind tool schemas to the underlying chat model (if supported).
        Returns a bound model instance.
        """
        if not hasattr(self.client, "bind_tools"):
            raise RuntimeError("This LLM client does not support tool binding.")
        tools = self.get_tool_defs(tool_names)
        return self.client.bind_tools(tools)

    async def invoke_with_tools(
        self,
        prompt: str,
        tool_names: Optional[Sequence[str]] = None,
        max_tool_iters: int = 3,
        **kwargs: Any,
    ) -> str:
        """
        Simple tool-calling loop for chat models using OpenAI-style tool schemas.
        """
        if not self.use_chat:
            raise RuntimeError("Tool calling requires a chat model (use_chat=True).")

        try:
            from langchain_core.messages import HumanMessage, ToolMessage
        except Exception as exc:
            raise ImportError(
                "langchain_core is required for tool calling."
            ) from exc

        try:
            from function_calling import execute_tool
        except Exception as exc:
            raise ImportError(
                "Unable to load tool executors from function_calling."
            ) from exc

        llm = self.bind_tools(tool_names)
        messages: List[Any] = [HumanMessage(content=prompt)]

        for _ in range(max_tool_iters):
            ai_msg = llm.invoke(messages, **kwargs)
            messages.append(ai_msg)

            tool_calls = getattr(ai_msg, "tool_calls", None) or []
            if not tool_calls:
                return getattr(ai_msg, "content", ai_msg)

            for call in tool_calls:
                name = call.get("name")
                args = call.get("args", {}) or {}
                tool_call_id = call.get("id")
                result = await execute_tool(name, **args)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call_id)
                )

        # Fallback: return last model content if max iterations reached
        return getattr(messages[-1], "content", messages[-1])

    def update_config(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        use_chat: Optional[bool] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if model_name is not None:
            self.model_name = model_name
        if base_url is not None:
            self.base_url = base_url
        if temperature is not None:
            self.temperature = temperature
        if use_chat is not None:
            self.use_chat = use_chat
        if extra:
            self.kwargs.update(extra)
        self.client = self._init_client()
