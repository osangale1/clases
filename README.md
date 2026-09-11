# RAG local con ChromaDB

Pre-entrega 3. Indexa los documentos de `data/` en ChromaDB y responde
preguntas usando solo esa info (si no esta ahi, dice que no sabe).

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Copiar `.env.example` a `.env`. `OPENAI_API_KEY` es obligatoria (se usa
para los embeddings, incluso si `LLM_PROVIDER=anthropic`). `LLM_PROVIDER`
define quien genera la respuesta (anthropic u openai).

## Uso

```bash
python ingest.py
python test_rag.py
```

`ingest.py` no reindexa si ya existe `./vectorstore` (usar `--forzar` para
reindexar despues de cambiar `data/`).
