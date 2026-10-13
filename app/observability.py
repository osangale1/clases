import logging
import os

from app import config

logger = logging.getLogger("sistema")


def setup_logging() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def setup_observability() -> None:
    if config.PHOENIX_ENABLED:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from phoenix.otel import register

        tracer_provider = register(
            project_name=config.PHOENIX_PROJECT,
            endpoint=config.PHOENIX_ENDPOINT,
            auto_instrument=False,
        )
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("trazas -> Phoenix (%s)", config.PHOENIX_ENDPOINT)
    elif os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true":
        logger.info("trazas -> LangSmith (proyecto %s)", os.environ.get("LANGCHAIN_PROJECT", "default"))
    else:
        logger.warning("sin plataforma de trazas configurada (ni Phoenix ni LangSmith)")
