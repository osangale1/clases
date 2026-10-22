from types import SimpleNamespace

import pytest

from app import config
from app.agents.analyst_agent import analizar_sentimiento, calcular_costo_tokens
from app.agents.research_agent import buscar_en_documentos
from app.llm import get_llm
from app.rag import ingest
from app.rag.embeddings import TAMANO_LOTE, GeminiEmbeddings, get_embeddings
from app.schemas import DecisionSupervisor, RespuestaFinal


class ModelosFalsos:
    """Imita client.models / client.aio.models de google-genai y guarda lo que recibe."""

    def __init__(self, dimension: int = 4, agregado: bool = False):
        self.dimension = dimension
        self.agregado = agregado
        self.llamadas = []

    def _responder(self, model, contents, config_embedding):
        self.llamadas.append((model, contents, config_embedding))
        cantidad = 1 if self.agregado else len(contents)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.5] * self.dimension) for _ in range(cantidad)])

    def embed_content(self, *, model, contents, config):
        return self._responder(model, contents, config)


class ModelosAsyncFalsos(ModelosFalsos):
    async def embed_content(self, *, model, contents, config):
        return self._responder(model, contents, config)


def embeddings_con_cliente_falso(agregado: bool = False, dimension: int = 4):
    sync = ModelosFalsos(dimension, agregado)
    asincrono = ModelosAsyncFalsos(dimension, agregado)
    emb = GeminiEmbeddings("gemini-embedding-2", dimension)
    emb._cliente = SimpleNamespace(models=sync, aio=SimpleNamespace(models=asincrono))
    return emb, sync, asincrono


def textos_de(contents) -> list[str]:
    return [c.parts[0].text for c in contents]


# ---- LLM ----
def test_get_llm_google(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "clave-de-prueba")

    llm = get_llm()

    assert type(llm).__name__ == "ChatGoogleGenerativeAI"
    assert llm.model.endswith(config.GOOGLE_MODEL)


def test_get_llm_proveedor_desconocido(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "inexistente")
    with pytest.raises(ValueError):
        get_llm()


def test_herramientas_y_salidas_estructuradas_son_compatibles_con_gemini(monkeypatch):
    """Sin red: la conversion de los esquemas Pydantic al formato de Gemini no debe romperse."""
    monkeypatch.setattr(config, "LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "clave-de-prueba")
    llm = get_llm()

    llm.bind_tools([buscar_en_documentos, analizar_sentimiento, calcular_costo_tokens])
    llm.with_structured_output(DecisionSupervisor)
    llm.with_structured_output(RespuestaFinal)


# ---- embeddings ----
def test_get_embeddings_segun_proveedor(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "google")
    assert isinstance(get_embeddings(), GeminiEmbeddings)

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "openai")
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "text-embedding-3-small")
    assert type(get_embeddings()).__name__ == "OpenAIEmbeddings"

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "otro")
    with pytest.raises(ValueError):
        get_embeddings()


def test_documentos_van_uno_por_content_con_prefijo_y_dimension():
    emb, sync, _ = embeddings_con_cliente_falso()

    vectores = emb.embed_documents(["uno", "dos", "tres"])

    assert len(vectores) == 3
    model, contents, cfg = sync.llamadas[0]
    assert model == "gemini-embedding-2"
    assert textos_de(contents) == ["title: none | text: uno", "title: none | text: dos", "title: none | text: tres"]
    assert cfg.output_dimensionality == 4
    assert cfg.task_type is None, "gemini-embedding-2 no acepta task_type"


def test_consulta_usa_el_prefijo_de_busqueda():
    emb, sync, _ = embeddings_con_cliente_falso()

    vector = emb.embed_query("que es RAG?")

    assert len(vector) == 4
    assert textos_de(sync.llamadas[0][1]) == ["task: search result | query: que es RAG?"]


async def test_version_async_tiene_el_mismo_contrato():
    emb, _, asincrono = embeddings_con_cliente_falso()

    docs = await emb.aembed_documents(["uno", "dos"])
    consulta = await emb.aembed_query("hola")

    assert len(docs) == 2 and len(consulta) == 4
    assert textos_de(asincrono.llamadas[0][1]) == ["title: none | text: uno", "title: none | text: dos"]
    assert textos_de(asincrono.llamadas[1][1]) == ["task: search result | query: hola"]


def test_lotes_respetan_el_tamano_maximo():
    emb, sync, _ = embeddings_con_cliente_falso()

    vectores = emb.embed_documents([f"texto {i}" for i in range(TAMANO_LOTE * 2 + 20)])

    assert len(vectores) == TAMANO_LOTE * 2 + 20
    assert [len(c[1]) for c in sync.llamadas] == [TAMANO_LOTE, TAMANO_LOTE, 20]


def test_si_gemini_devuelve_un_embedding_agregado_falla_con_error_claro():
    emb, _, _ = embeddings_con_cliente_falso(agregado=True)

    with pytest.raises(ValueError, match="embeddings para 3 textos"):
        emb.embed_documents(["uno", "dos", "tres"])


# ---- indice de Pinecone ----
def pinecone_falso(indices: dict[str, int]):
    creados = []

    class Cliente:
        def list_indexes(self):
            return [{"name": n} for n in indices]

        def describe_index(self, nombre):
            return SimpleNamespace(dimension=indices[nombre], status={"ready": True})

        def create_index(self, **kwargs):
            creados.append(kwargs)
            indices[kwargs["name"]] = kwargs["dimension"]

    return Cliente(), creados


def test_indice_con_otra_dimension_falla_antes_de_subir_nada(monkeypatch):
    cliente, creados = pinecone_falso({config.INDEX_NAME: 1536})
    monkeypatch.setattr(ingest, "get_pinecone_client", lambda: cliente)
    monkeypatch.setattr(config, "EMBEDDING_DIMENSION", 768)

    with pytest.raises(ValueError, match="dimension 1536"):
        ingest.asegurar_indice()
    assert creados == []


def test_indice_con_la_dimension_correcta_se_reutiliza(monkeypatch):
    cliente, creados = pinecone_falso({config.INDEX_NAME: 768})
    monkeypatch.setattr(ingest, "get_pinecone_client", lambda: cliente)
    monkeypatch.setattr(config, "EMBEDDING_DIMENSION", 768)

    ingest.asegurar_indice()
    assert creados == []


def test_indice_inexistente_se_crea_con_la_dimension_configurada(monkeypatch):
    cliente, creados = pinecone_falso({})
    monkeypatch.setattr(ingest, "get_pinecone_client", lambda: cliente)
    monkeypatch.setattr(config, "EMBEDDING_DIMENSION", 768)

    ingest.asegurar_indice()

    assert creados[0]["dimension"] == 768
    assert creados[0]["metric"] == "cosine"


# ---- VECTOR_STORE=memory (sin Pinecone) ----
async def test_modo_memoria_indexa_al_arrancar_sin_pinecone(monkeypatch):
    from langchain_core.embeddings import DeterministicFakeEmbedding

    import app.rag.service as m_service
    from app.rag.service import RAGService

    monkeypatch.setattr(config, "VECTOR_STORE", "memory")
    monkeypatch.setattr(m_service, "get_embeddings", lambda: DeterministicFakeEmbedding(size=16))

    def pinecone_no_se_usa():
        raise AssertionError("en modo memoria no se tiene que tocar Pinecone")

    monkeypatch.setattr(m_service, "crear_vectorstore", pinecone_no_se_usa)

    servicio = await RAGService.crear()
    fragmentos = await servicio.buscar("RediSearch")
    assert "redis.md" in {f.fuente for f in fragmentos}


async def test_ingest_en_modo_memoria_no_sube_nada(monkeypatch):
    monkeypatch.setattr(config, "VECTOR_STORE", "memory")
    monkeypatch.setattr(ingest, "get_pinecone_client", lambda: (_ for _ in ()).throw(AssertionError("no")))

    await ingest.ingestar()
