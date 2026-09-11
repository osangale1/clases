# RAG escalable con Pinecone

Pre-entrega 4. Sube documentos tecnicos a un indice Serverless de Pinecone
y los busca combinando BM25 (lexico) con busqueda vectorial.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Copiar `.env.example` a `.env` y completar `PINECONE_API_KEY` y
`OPENAI_API_KEY` (esta ultima se usa para los embeddings, 1536 dim).

## Replicar el indice

```bash
python pinecone_setup.py
python ingest.py
```

`ingest.py` no reindexa si el namespace ya tiene vectores cargados (usa
`--forzar` si cambiaste `data/`).

## Evaluar

```bash
python evaluate.py
```

Imprime Recall@5 y Precision@5 sobre las 5 preguntas de `golden_set.json`.
