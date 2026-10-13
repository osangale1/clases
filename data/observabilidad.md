# Observabilidad

Un sistema con agentes sin trazas es una caja negra: se ve la respuesta pero
no por que el supervisor eligio a un agente, que herramienta se llamo ni
cuantos tokens se gastaron.

Arize Phoenix y LangSmith guardan una traza por ejecucion, con un span por
cada nodo, llamada al LLM y herramienta. Desde ahi se ve la latencia (por
ejemplo el p95), el costo calculado a partir de los tokens de entrada y
salida, y el nodo que mas consume.

Ademas de las trazas conviene dejar logs con el job_id de cada tarea, para
poder cruzar lo que paso en la API con lo que se ve en el dashboard.
