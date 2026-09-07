import json

from hybrid_retriever import RAGSystem

TOP_K = 5


def cargar_golden_set(ruta: str = "golden_set.json"):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluar() -> None:
    """
    Para cada pregunta del golden set, busca los top-5 y ve si el documento
    esperado aparece entre esos 5. Como solo conocemos UN documento
    relevante por pregunta:
      - Recall@5    = 1 si el documento esperado aparece entre los 5, 0 si no.
      - Precision@5 = cuantos de esos 5 son del documento esperado, sobre 5.
    """
    sistema = RAGSystem()
    golden_set = cargar_golden_set()

    recalls = []
    precisiones = []

    print("Resultados por pregunta:\n")
    for caso in golden_set:
        pregunta = caso["pregunta"]
        esperado = caso["documento_id_esperado"]

        resultados = sistema.buscar(pregunta)
        fuentes_recuperadas = [doc.metadata.get("fuente") for doc in resultados]
        coincidencias = fuentes_recuperadas.count(esperado)

        recall = 1 if coincidencias > 0 else 0
        precision = coincidencias / TOP_K

        recalls.append(recall)
        precisiones.append(precision)

        print(f"- Pregunta: {pregunta}")
        print(f"  Esperado: {esperado}")
        print(f"  Recuperados: {fuentes_recuperadas}")
        print(f"  Recall@5: {recall} | Precision@5: {precision:.2f}\n")

    recall_promedio = sum(recalls) / len(recalls)
    precision_promedio = sum(precisiones) / len(precisiones)

    print("=== Resumen ===")
    print(f"Preguntas evaluadas:  {len(golden_set)}")
    print(f"Recall@5 promedio:    {recall_promedio:.2f}")
    print(f"Precision@5 promedio: {precision_promedio:.2f}")


if __name__ == "__main__":
    evaluar()
