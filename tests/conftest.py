import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("PINECONE_API_KEY", "test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ["PHOENIX_ENABLED"] = "false"
os.environ["CARPETA_DATOS"] = str(RAIZ / "data")

import asyncio  # noqa: E402

import pytest  # noqa: E402
from langchain_core.embeddings import DeterministicFakeEmbedding  # noqa: E402
from langchain_core.vectorstores import InMemoryVectorStore  # noqa: E402

import app.agents.analyst_agent as m_analista  # noqa: E402
import app.agents.research_agent as m_investigador  # noqa: E402
import app.graph as m_graph  # noqa: E402
from app.rag.documentos import cargar_y_fragmentar  # noqa: E402
from app.rag.retriever import construir_retriever  # noqa: E402
from app.rag.service import RAGService, set_servicio  # noqa: E402
from tests import fakes  # noqa: E402


@pytest.fixture(autouse=True)
def llm_falso(monkeypatch):
    fakes.reset()
    for modulo in (m_graph, m_analista, m_investigador):
        monkeypatch.setattr(modulo, "get_llm", lambda: fakes.FakeLLM())
    m_graph.get_agente_investigador.cache_clear()
    m_graph.get_agente_analista.cache_clear()

    yield

    m_graph.get_agente_investigador.cache_clear()
    m_graph.get_agente_analista.cache_clear()
    # en cada test se verifica que nunca se le mande al LLM un ultimo mensaje del asistente
    assert fakes.ERRORES_PREFILL == []


async def crear_servicio_falso() -> RAGService:
    fragmentos = await asyncio.to_thread(cargar_y_fragmentar)
    vectorstore = InMemoryVectorStore(DeterministicFakeEmbedding(size=64))
    await vectorstore.aadd_documents(fragmentos)
    return RAGService(construir_retriever(fragmentos, vectorstore))


@pytest.fixture
async def servicio_rag():
    servicio = await crear_servicio_falso()
    set_servicio(servicio)
    yield servicio
    set_servicio(None)
