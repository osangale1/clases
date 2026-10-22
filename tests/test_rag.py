from pathlib import Path

from app import config
from app.rag.documentos import cargar_y_fragmentar
from app.rag.retriever import tokenizar

RAIZ = Path(__file__).resolve().parent.parent


def test_chunking_cubre_todos_los_documentos_con_metadatos():
    fragmentos = cargar_y_fragmentar()
    archivos = {p.name for p in (RAIZ / "data").glob("*.md")}

    assert {f.metadata["fuente"] for f in fragmentos} == archivos
    for f in fragmentos:
        assert set(f.metadata) == {"fuente", "pagina", "categoria"}
        assert f.metadata["categoria"] != "general", f"falta categoria para {f.metadata['fuente']}"
        assert f.metadata["pagina"] >= 1


def test_tokenizador_ignora_mayusculas_acentos_y_puntuacion():
    assert tokenizar("RediSearch. Búsqueda, vectorial!") == ["redisearch", "busqueda", "vectorial"]


def test_retriever_es_hibrido_bm25_mas_vectorial(servicio_rag):
    ensemble = servicio_rag.retriever
    assert len(ensemble.retrievers) == 2
    assert type(ensemble.retrievers[0]).__name__ == "BM25Retriever"
    assert ensemble.weights == [0.5, 0.5]


async def test_parte_lexica_encuentra_termino_tecnico_exacto(servicio_rag):
    # RediSearch aparece solo en redis.md: BM25 lo tiene que poner primero.
    # (los embeddings del test son falsos, por eso no se mide el ranking vectorial)
    bm25 = servicio_rag.retriever.retrievers[0]
    resultados = await bm25.ainvoke("RediSearch")
    assert resultados[0].metadata["fuente"] == "redis.md"

    fuentes = {f.fuente for f in await servicio_rag.buscar("RediSearch")}
    assert "redis.md" in fuentes


async def test_retriever_respeta_top_k(servicio_rag):
    fragmentos = await servicio_rag.buscar("base de datos vectorial y busqueda")
    assert 1 <= len(fragmentos) <= config.TOP_K


async def test_retriever_devuelve_fragmentos_validados(servicio_rag):
    for f in await servicio_rag.buscar("FastAPI async"):
        assert f.fuente.endswith(".md")
        assert f.texto
