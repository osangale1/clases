import asyncio
import os

from dotenv import load_dotenv

from clients import AsyncLLMManager
from schemas import ChatMessage, ModelConfig

load_dotenv()

PREGUNTA = "¿Qué es la entropía?"


async def probar_proveedor(provider: str, model: str) -> None:
    manager = AsyncLLMManager(provider=provider)
    messages = [ChatMessage(role="user", content=PREGUNTA)]
    config = ModelConfig(model=model, temperature=0.7, max_tokens=300)

    print(f"\n=== {provider.upper()} — modo normal ===")
    response = await manager.generate(messages, config)
    print(response.content)

    print(f"\n=== {provider.upper()} — modo streaming ===")
    async for chunk in manager.generate_stream(messages, config):
        print(chunk, end="", flush=True)
    print()


async def main() -> None:
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")

    if os.environ.get("OPENAI_API_KEY"):
        await probar_proveedor("openai", openai_model)
    else:
        print("OPENAI_API_KEY no configurada, se omite la prueba de OpenAI.")

    if os.environ.get("ANTHROPIC_API_KEY"):
        await probar_proveedor("anthropic", anthropic_model)
    else:
        print("ANTHROPIC_API_KEY no configurada, se omite la prueba de Anthropic.")


if __name__ == "__main__":
    asyncio.run(main())
