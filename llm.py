import os


def get_llm():
    proveedor = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if proveedor == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-5"), temperature=0)

    raise ValueError(f"proveedor no soportado: {proveedor}")
