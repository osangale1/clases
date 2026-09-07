# Sistema RAG escalable en la nube con Pinecone

Pre-entrega 4. Sube documentos tecnicos a un indice Serverless de Pinecone,
los busca con un recuperador hibrido (BM25 + vectorial) y mide que tan bien
recupera con un pequeño golden set (Precision@5 / Recall@5).

## Estructura

- `data/`: 5 archivos `.md` de ejemplo, notas sobre una libreria de Python
  para hacer peticiones HTTP (GET/POST, auth, sesiones, errores, JSON).
- `embeddings.py`: un solo lugar para armar los embeddings (mismo modelo
  para indexar y para consultar).
- `pinecone_setup.py`: crea el indice Serverless si no existe (dim=1536).
- `ingest.py`: carga `data/`, hace chunking y sube los fragmentos a Pinecone
  con metadatos avanzados (fuente, pagina, categoria). También expone
  `cargar_y_fragmentar()`, que reusa `hybrid_retriever.py` para el BM25.
- `hybrid_retriever.py`: clase `RAGSystem`, junta un `BM25Retriever` (lexico)
  con el retriever vectorial de Pinecone usando `EnsembleRetriever`.
- `golden_set.json`: 5 preguntas con el documento que deberia responderlas.
- `evaluate.py`: corre esas 5 preguntas y calcula Precision@5 / Recall@5.

## Instalacion

Requiere Python 3.12+ y una cuenta de [Pinecone](https://www.pinecone.io/)
(el free tier alcanza para esto).

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

- `PINECONE_API_KEY`: API key de tu cuenta de Pinecone.
- `INDEX_NAME`: nombre del indice (default `curso-rag-index`).
- `PINECONE_CLOUD` / `PINECONE_REGION`: donde se crea el indice Serverless
  (default `aws` / `us-east-1`).
- `OPENAI_API_KEY`: **obligatoria**, se usa para generar los embeddings
  (1536 dimensiones, tiene que coincidir con la dimension del indice).
- `EMBEDDING_MODEL`: default `text-embedding-3-small`.

## Como replicar el indice

```bash
python pinecone_setup.py   # crea el indice si no existe (idempotente)
python ingest.py           # carga data/, chunkea y sube a Pinecone
```

`ingest.py` primero se fija si el namespace `documentacion-tecnica` ya tiene
vectores cargados; si ya tiene, no vuelve a indexar (para reindexar de
nuevo despues de cambiar `data/`: `python ingest.py --forzar`).

## Evaluar

```bash
python evaluate.py
```

Imprime, por cada una de las 5 preguntas del golden set, los documentos
recuperados y el Recall@5 / Precision@5 de esa pregunta, y al final un
resumen con el promedio.

## Como funciona

1. `cargar_y_fragmentar()` (en `ingest.py`) parte cada `.md` en chunks de
   ~600 tokens con 60 de overlap (ni tan chico que pierda contexto, ni tan
   grande que diluya el embedding), y les agrega metadatos: `fuente`
   (archivo de origen), `pagina` (numero de fragmento dentro del archivo) y
   `categoria` (tema, asignado por archivo).
2. `ingest.py` sube esos fragmentos a Pinecone con `PineconeVectorStore`,
   siempre en el namespace `documentacion-tecnica` (asi el dia de mañana que
   se agreguen otros datos al mismo indice, las busquedas no se mezclan). El
   texto original queda guardado dentro de los metadatos del vector, no hace
   falta ir a buscarlo a otra base de datos.
3. `RAGSystem` (en `hybrid_retriever.py`) arma dos retrievers sobre los
   mismos chunks: un `BM25Retriever` (busqueda lexica, por palabra exacta,
   buena para nombres de headers o metodos) y el retriever vectorial de
   Pinecone (busqueda semantica). Los combina con `EnsembleRetriever` y
   devuelve el top-5 final.
4. `evaluate.py` corre el golden set contra `RAGSystem.buscar()` y calcula,
   por pregunta, si el documento esperado aparece entre los 5 recuperados
   (Recall@5) y que porcentaje de esos 5 son justamente ese documento
   (Precision@5). Al final promedia todo y lo imprime en consola.

## Resumen de metricas (referencia)

Con el dataset de ejemplo de `data/` y las 5 preguntas de `golden_set.json`,
cada pregunta tiene un unico documento fuente y ese documento genera pocos
fragmentos, asi que lo esperable es Recall@5 = 1.00 (el documento correcto
aparece siempre entre los 5) y un Precision@5 mas bajo (de los 5 lugares,
solo 1 o 2 van a ser realmente del documento esperado, el resto son de los
otros archivos). Los numeros reales dependen de tu cuenta de Pinecone y se
imprimen al correr `python evaluate.py`.
