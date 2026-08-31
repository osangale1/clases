# Sistema de recuperacion semantica local (RAG)

Pre-entrega 3. Toma unos documentos tecnicos (`data/`), los indexa en una
ChromaDB local y responde preguntas basandose SOLO en lo que encuentra ahi.
Si no encuentra nada relevante, el modelo tiene que decir que no sabe (nada
de inventar).

## Estructura

- `data/`: 4 archivos `.md` de ejemplo, manual ficticio de una API de tareas
  (autenticacion, endpoints, errores, despliegue).
- `embeddings.py`: un solo lugar donde se arman los embeddings, para usar
  siempre el mismo modelo al indexar y al consultar.
- `ingest.py`: lee `data/`, fragmenta los documentos (chunking) y los guarda
  en ChromaDB (`./vectorstore`).
- `rag_chain.py`: el retriever + el prompt + el LLM armados con LCEL, salida
  parseada con `PydanticOutputParser`, y la funcion async `get_rag_response()`.
- `test_rag.py`: mini-script de prueba con una pregunta normal y una trampa.

## Instalacion

Requiere Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

```bash
cp .env.example .env
```

Variables (`.env`):

- `OPENAI_API_KEY`: **obligatoria siempre**, se usa para los embeddings
  (Anthropic no tiene API de embeddings propia, asi que aunque generes las
  respuestas con Claude, para indexar y buscar se usa OpenAI).
- `EMBEDDING_MODEL`: modelo de embeddings (default `text-embedding-3-small`).
- `LLM_PROVIDER`: `anthropic` u `openai`, quien genera la respuesta final
  (default `anthropic`).
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`: si `LLM_PROVIDER=anthropic`.
- `OPENAI_MODEL`: si `LLM_PROVIDER=openai`.

## Uso

Primero indexar los documentos (solo hace falta una vez, no vuelve a
indexar si ya existe `./vectorstore`):

```bash
python ingest.py
```

Si cambiaste algo en `data/` y queres reindexar todo de nuevo:

```bash
python ingest.py --forzar
```

Despues corres las pruebas:

```bash
python test_rag.py
```

## Como funciona

1. `ingest.py` carga los `.txt`/`.md` de `data/`, los corta en fragmentos de
   500 tokens con 50 de overlap (`RecursiveCharacterTextSplitter`) y los
   guarda en una coleccion de ChromaDB persistida en `./vectorstore`.
2. `rag_chain.get_retriever()` arma un retriever sobre esa misma coleccion,
   trayendo los 4 fragmentos mas parecidos a la pregunta (`top_k=4`, ni uno
   solo ni "contexto infinito").
3. Esos fragmentos se juntan en un solo texto marcando de que archivo salio
   cada uno (`formatear_contexto`).
4. El prompt (`ChatPromptTemplate`) le dice al modelo que responda SOLO con
   ese contexto, y que si la respuesta no esta ahi lo diga en vez de
   inventar.
5. La cadena LCEL (`retriever + prompt + llm + PydanticOutputParser`)
   devuelve un objeto `RespuestaRAG` con `respuesta` y `fuentes`.
6. `get_rag_response(query)` corre todo eso de forma asincrona
   (`.ainvoke()`) y deja logs de la consulta y las fuentes usadas.

## Prueba de estres

`test_rag.py` hace dos preguntas:

1. Una que si tiene respuesta en `data/` (que header de autenticacion usa la API).
2. Una "trampa" que no esta en ningun documento (contraseña de una base de
   datos que no existe en los docs), para chequear que el modelo no
   alucine una respuesta y devuelva `fuentes` vacio.
