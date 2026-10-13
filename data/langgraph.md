# LangGraph

LangGraph permite armar agentes como grafos de estado. Cada nodo es una
funcion que recibe el estado y devuelve cambios, y las aristas (que pueden
ser condicionales) deciden cual es el siguiente nodo.

Un patron comun es el supervisor: un nodo central decide a que agente
especialista mandar la tarea, recibe el resultado, y decide si falta algo o
si ya se puede terminar. Es facil de seguir porque todo el control pasa por
un solo lugar, pero hay que poner un limite de pasos para evitar loops.

Con un checkpointer el estado se guarda por thread_id, y eso permite
retomar conversaciones y pausar la ejecucion para pedir aprobacion humana
(human in the loop) con interrupt.
