# Corridas reales con Gemini (tier gratuito) - 2026-10-22

Corridas contra la API de Google real (no LLM falso), con Redis Stack y Phoenix en Docker y
`VECTOR_STORE=memory` (embeddings reales de `gemini-embedding-2`, indice en memoria; Pinecone no
participo en estas corridas).

## Resultados

| Que se corrio | Modelo | Resultado |
| --- | --- | --- |
| Embeddings de 3 documentos + 1 consulta | `gemini-embedding-2` (768 dim) | OK. La consulta "donde se guarda el estado de las tareas?" quedo mas cerca del documento de Redis (coseno 0.757 vs 0.582 y 0.618) |
| Prueba 1 de `scripts/pruebas.py` por la API (RAG) | `gemini-3.6-flash` | `DONE`: supervisor -> investigador -> FINISH -> sintesis, fuente `rag.md`. Traza: `screenshots/phoenix_gemini_real_traza_rag.png` |
| Analista con herramienta `calcular_costo_tokens` | `gemini-3.8-flash` | OK: llamo a la herramienta y respondio 0.0081 USD |
| Investigador con `buscar_en_documentos` (RAG hibrido real) | `gemini-3.8-flash` | OK: llamo a la herramienta y cito Redis |
| Tarea "busca info de Redis y analiza el sentimiento" (grafo completo) | `gemini-3.5-flash-lite` | OK despues de los fixes de abajo: investigador -> analista -> FINISH -> sintesis, fuente `redis.md` |

Phoenix (proyecto `sistema-final-gemini-real`): 18 llamadas al LLM trazadas con 26 071 tokens reales.
El costo que muestra Phoenix es una estimacion con precio de lista; en el tier gratuito no se cobra.

## Problemas reales encontrados (y corregidos)

1. `gemini-2.5-flash` ya no esta disponible para cuentas nuevas (404). Se cambio el modelo por defecto.
2. El supervisor volvia a elegir al investigador aunque ya hubiera aportado: los aportes le llegaban
   como mensajes del asistente sin rotulo. Ahora recibe un resumen de quien aporto que y quien falta
   (`resumen_contribuciones` en `app/graph.py`).
3. El modelo cerro con FINISH diciendo que el analista ya habia analizado, sin que el analista
   participara. Se agrego una validacion en codigo: si el usuario pidio un analisis o calculo y el
   analista no aporto, el FINISH se rechaza y se deriva al analista.

Los tres quedaron cubiertos por tests (`tests/test_graph.py`).

## Limites del tier gratuito (medidos)

- Cupo por modelo y proyecto: 20 pedidos por dia y 5 por minuto (`gemini-3.6-flash`, segun el 429 de Google).
- Cada tarea usa entre 5 y 8 pedidos al LLM: con un solo modelo entran ~3 tareas por dia.
- Hubo 503 ("high demand") frecuentes en los modelos flash.
- Por eso no se pudieron correr las 7 pruebas completas con modelo real en el mismo dia. Para
  completarlas: esperar a que se renueve el cupo (medianoche hora del Pacifico) o repartir las
  pruebas entre modelos cambiando `GOOGLE_MODEL`.
