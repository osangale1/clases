# Manejo de errores

Por defecto, una respuesta con codigo de error (4xx o 5xx) no lanza una
excepcion automaticamente: hay que revisar el `status_code` a mano o llamar
a un metodo tipo `raise_for_status()` para que si la levante.

Para timeouts, siempre hay que pasar un valor explicito (por ejemplo
`timeout=5`), porque si no se especifica, la peticion puede quedar colgada
para siempre esperando al servidor.

Ante errores de red (timeout, conexion rechazada, DNS), conviene reintentar
con backoff exponencial en vez de fallar directo al primer intento.
