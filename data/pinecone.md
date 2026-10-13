# Pinecone

Pinecone es una base de datos vectorial administrada. En su modo serverless
no hay que dimensionar servidores: se crea un indice con una dimension fija
(tiene que coincidir con la del modelo de embeddings, por ejemplo 1536) y
una metrica, normalmente coseno.

Conviene separar los datos por namespace, para que busquedas de distintos
tipos de datos no se mezclen. Los metadatos (fuente, pagina, categoria) se
guardan junto al vector y permiten filtrar y citar de donde sale cada
respuesta.

Una busqueda hibrida combina la similitud vectorial de Pinecone con una
busqueda lexica tipo BM25, que ayuda con nombres propios y terminos
tecnicos exactos.
