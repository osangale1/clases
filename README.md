# Agente ReAct con memoria persistente

Pre-entrega 5. Agente con LangGraph que decide solo cuando usar una
herramienta, puede encadenar mas de una para llegar a la respuesta, y
recuerda la conversacion por `thread_id` (checkpointer en SQLite).

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Copiar `.env.example` a `.env`. `LLM_PROVIDER` puede ser `anthropic` u
`openai`.

## Uso

```bash
python test_agent.py
```

Corre 3 casos (razonamiento multi-paso con 2 herramientas, memoria entre
turnos con el mismo `thread_id`, y un cliente inexistente para probar que
el agente no invente datos) y guarda la traza completa en
`traza_ejecucion.json`.

## traza_ejemplo.json

Es un ejemplo del formato de traza, armado a mano porque no tenia API key
al preparar el repo (los resultados de las herramientas si son reales,
no dependen de ningun LLM). Corriendo `test_agent.py` con tu propia key se
genera la traza real en `traza_ejecucion.json`.
