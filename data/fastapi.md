# FastAPI

FastAPI es un framework para armar APIs en Python con tipado y validacion
automatica usando Pydantic. Genera sola la documentacion interactiva en
/docs.

Para tareas largas (como correr un agente) el endpoint no debe esperar el
resultado: encola el trabajo, devuelve un job_id enseguida, y el cliente
consulta el estado con otro endpoint. Si la tarea falla en segundo plano,
hay que capturar la excepcion y guardar el estado FAILED, si no el cliente
queda esperando para siempre.

Dentro de funciones async no se deben usar librerias bloqueantes (como
requests): hay que usar httpx o los clientes async oficiales, porque
bloquean el event loop y frenan a todos los demas pedidos.
