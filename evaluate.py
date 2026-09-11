import json

from hybrid_retriever import RAGSystem

TOP_K = 5


def cargar_golden_set(ruta: str = "golden_set.json"):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluar() -> None:
    sistema = RAGSystem()
    golden_set = cargar_golden_set()

    recalls = []
    precisiones = []

    for caso in golden_set:
        resultados = sistema.buscar(caso["pregunta"])
        fuentes = [doc.metadata.get("fuente") for doc in resultados]
        coincidencias = fuentes.count(caso["documento_id_esperado"])

        recalls.append(1 if coincidencias > 0 else 0)
        precisiones.append(coincidencias / TOP_K)

        print(caso["pregunta"])
        print("esperado:", caso["documento_id_esperado"], "| recuperados:", fuentes)

    print("Recall@5:", sum(recalls) / len(recalls))
    print("Precision@5:", sum(precisiones) / len(precisiones))


if __name__ == "__main__":
    evaluar()
