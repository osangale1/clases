# Redis

Redis es una base de datos en memoria, muy rapida, que tambien puede
persistir los datos en disco. En este sistema se usa para dos cosas: guardar
el estado de cada job (PENDING, RUNNING, DONE, FAILED) y guardar los
checkpoints de LangGraph.

Para que el checkpointer de LangGraph funcione hace falta Redis Stack, que
incluye el modulo de busqueda RediSearch. Redis normal no alcanza.

Con persistencia activada (appendonly), las conversaciones no se pierden si
el servidor se reinicia.
