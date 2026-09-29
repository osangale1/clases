import os

from dotenv import load_dotenv

load_dotenv()


def setup_observability():
    if os.environ.get("PHOENIX_ENABLED", "false").lower() == "true":
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        register(endpoint=os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"))
        LangChainInstrumentor().instrument()
        return

    # si no usas phoenix, con LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY en el .env
    # LangSmith traza solo, no hace falta codigo extra aca
