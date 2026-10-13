# RAG (Retrieval Augmented Generation)

RAG combina un buscador con un modelo de lenguaje. Primero se recuperan los
fragmentos de documentos mas parecidos a la pregunta, y despues el modelo
responde usando solo esos fragmentos como contexto.

Sirve para reducir alucinaciones, porque el modelo no responde de memoria
sino con informacion concreta. Si el contexto no tiene la respuesta, lo
correcto es decir que no se sabe.

Un buen RAG cuida el tamaño de los chunks (ni muy chicos ni muy grandes), usa
siempre el mismo modelo de embeddings para indexar y consultar, y limita la
cantidad de fragmentos que se le pasan al modelo (top_k de 3 a 5).
