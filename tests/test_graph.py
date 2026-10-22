from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app import config
from app.graph import armar_grafo
from app.hitl import es_critico
from tests import fakes
from tests.fakes import decide, final, texto, tool_call


def entrada(pregunta: str) -> dict:
    return {
        "messages": [HumanMessage(content=pregunta)],
        "pasos": 0,
        "contribuciones": {},
        "aprobado": False,
        "respuesta_final": {},
    }


def config_hilo(thread_id: str = "t1") -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": config.RECURSION_LIMIT}


def compilar():
    return armar_grafo().compile(checkpointer=InMemorySaver())


def test_es_critico():
    assert es_critico("Es IMPORTANTE revisar esto")
    assert es_critico("cambio en produccion")
    assert not es_critico("que es RAG?")


async def test_flujo_rag_supervisor_investigador_sintesis(servicio_rag):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "RAG alucinaciones"}, "c1"),
            texto("RAG recupera fragmentos y responde con ellos. Fuente: rag.md"),
            decide("FINISH"),
            final("RAG reduce alucinaciones.", ["rag.md"]),
        ]
    )

    r = await compilar().ainvoke(entrada("Que es RAG?"), config=config_hilo())

    assert r["respuesta_final"] == {"respuesta": "RAG reduce alucinaciones.", "fuentes": ["rag.md"]}
    assert list(r["contribuciones"]) == ["investigador"]
    assert r["pasos"] == 2
    assert not fakes.COLA, "el guion se tiene que consumir completo"


async def test_flujo_con_analista_aporta_los_dos_agentes(servicio_rag):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "Pinecone"}, "c1"),
            texto("Pinecone es una DB vectorial. Fuente: pinecone.md"),
            decide("analista"),
            tool_call("analizar_sentimiento", {"texto": "Pinecone ayuda y es simple"}, "c2"),
            texto("Sentimiento positivo."),
            decide("FINISH"),
            final("Pinecone suena positivo.", ["pinecone.md"]),
        ]
    )

    r = await compilar().ainvoke(entrada("Info de Pinecone y analiza el sentimiento"), config=config_hilo())

    assert set(r["contribuciones"]) == {"investigador", "analista"}
    assert r["pasos"] == 3


async def test_tarea_critica_se_pausa_y_se_reanuda_al_aprobar(servicio_rag):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "Pinecone"}, "c1"),
            texto("Pinecone es una DB vectorial."),
            decide("analista"),
        ]
    )
    grafo = compilar()

    pausa = await grafo.ainvoke(entrada("Es importante: info de Pinecone y analiza"), config=config_hilo())
    assert pausa["__interrupt__"][0].value["pregunta"]
    assert "analista" not in pausa["contribuciones"]

    fakes.COLA.extend(
        [
            tool_call("analizar_sentimiento", {"texto": "Pinecone ayuda"}, "c2"),
            texto("Sentimiento positivo."),
            decide("FINISH"),
            final("Listo, aprobado y analizado.", ["pinecone.md"]),
        ]
    )
    r = await grafo.ainvoke(Command(resume="si"), config=config_hilo())

    assert set(r["contribuciones"]) == {"investigador", "analista"}
    assert r["respuesta_final"]["respuesta"] == "Listo, aprobado y analizado."


async def test_rechazo_humano_no_ejecuta_al_analista(servicio_rag):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "LangGraph"}, "c1"),
            texto("LangGraph arma grafos."),
            decide("analista"),
        ]
    )
    grafo = compilar()
    await grafo.ainvoke(entrada("Es critico: info de LangGraph y analiza"), config=config_hilo())

    fakes.COLA.append(final("Se rechazo la aprobacion.", ["langgraph.md"]))
    r = await grafo.ainvoke(Command(resume="no"), config=config_hilo())

    assert list(r["contribuciones"]) == ["investigador"]
    assert not fakes.COLA, "el analista no deberia haber consumido nada del guion"
    assert any("rechazada" in m.content for m in r["messages"])


async def test_tope_de_pasos_corta_el_bucle_del_supervisor(servicio_rag, monkeypatch):
    monkeypatch.setattr(config, "MAX_PASOS", 2)
    ronda = [
        decide("investigador"),
        tool_call("buscar_en_documentos", {"consulta": "Redis"}, "c"),
        texto("Redis guarda estado."),
    ]
    fakes.COLA.extend(ronda + ronda + [final("Corte por tope de pasos.", [])])

    r = await compilar().ainvoke(entrada("Que es Redis?"), config=config_hilo())

    assert r["respuesta_final"]["respuesta"] == "Corte por tope de pasos."
    assert r["pasos"] == 3


async def test_checkpointer_recuerda_la_conversacion_por_thread_id(servicio_rag):
    grafo = compilar()
    fakes.COLA.extend([decide("FINISH"), final("Primera respuesta.", [])])
    await grafo.ainvoke(entrada("hola"), config=config_hilo("conv-1"))

    fakes.VISTO.clear()
    fakes.COLA.extend([decide("FINISH"), final("Segunda respuesta.", [])])
    await grafo.ainvoke(entrada("y ahora?"), config=config_hilo("conv-1"))

    # el supervisor del segundo turno ve la historia del primero (>1 mensaje + instrucciones)
    assert fakes.VISTO[0][1] > 3

    fakes.VISTO.clear()
    fakes.COLA.extend([decide("FINISH"), final("Otra conversacion.", [])])
    await grafo.ainvoke(entrada("hola"), config=config_hilo("conv-2"))
    assert fakes.VISTO[0][1] < 4, "otro thread_id no deberia heredar la historia"
