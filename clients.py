import os
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from schemas import ChatMessage, ModelConfig, ModelResponse


class BaseLLMClient(ABC):
    """Interfaz comun para cualquier proveedor de LLM."""

    @abstractmethod
    async def generate(self, messages: List[ChatMessage], config: ModelConfig) -> ModelResponse:
        ...

    @abstractmethod
    def generate_stream(self, messages: List[ChatMessage], config: ModelConfig) -> AsyncGenerator[str, None]:
        ...


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    async def generate(self, messages: List[ChatMessage], config: ModelConfig) -> ModelResponse:
        try:
            response = await self.client.chat.completions.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[m.model_dump() for m in messages],
            )
            return ModelResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider="openai",
                usage=response.usage.model_dump() if response.usage else None,
            )
        except Exception as e:
            return ModelResponse(
                content=f"[Error OpenAI]: {e}",
                model=config.model,
                provider="openai",
            )

    async def generate_stream(self, messages: List[ChatMessage], config: ModelConfig) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[m.model_dump() for m in messages],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            yield f"[Error OpenAI]: {e}"


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    @staticmethod
    def _split_system(messages: List[ChatMessage]):
        # Anthropic recibe el system prompt aparte, no como un mensaje mas.
        system = "\n".join(m.content for m in messages if m.role == "system")
        rest = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        return system or None, rest

    async def generate(self, messages: List[ChatMessage], config: ModelConfig) -> ModelResponse:
        try:
            system, rest = self._split_system(messages)
            response = await self.client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                system=system,
                messages=rest,
            )
            text = "".join(block.text for block in response.content if block.type == "text")
            return ModelResponse(
                content=text,
                model=response.model,
                provider="anthropic",
                usage=response.usage.model_dump() if response.usage else None,
            )
        except Exception as e:
            return ModelResponse(
                content=f"[Error Anthropic]: {e}",
                model=config.model,
                provider="anthropic",
            )

    async def generate_stream(self, messages: List[ChatMessage], config: ModelConfig) -> AsyncGenerator[str, None]:
        try:
            system, rest = self._split_system(messages)
            async with self.client.messages.stream(
                model=config.model,
                max_tokens=config.max_tokens,
                system=system,
                messages=rest,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Error Anthropic]: {e}"


class AsyncLLMManager:
    """Elige el cliente segun el proveedor pedido (openai | anthropic)."""

    def __init__(self, provider: str, api_key: Optional[str] = None):
        provider = provider.lower()
        if provider == "openai":
            self.client: BaseLLMClient = OpenAIClient(api_key)
        elif provider == "anthropic":
            self.client = AnthropicClient(api_key)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}")
        self.provider = provider

    async def generate(self, messages: List[ChatMessage], config: ModelConfig) -> ModelResponse:
        return await self.client.generate(messages, config)

    async def generate_stream(self, messages: List[ChatMessage], config: ModelConfig) -> AsyncGenerator[str, None]:
        async for chunk in self.client.generate_stream(messages, config):
            yield chunk
