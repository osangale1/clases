# Codigos de error

- `400 Bad Request`: el cuerpo de la peticion no tiene el formato esperado.
- `401 Unauthorized`: falta el header `X-API-Key` o la clave es invalida.
- `404 Not Found`: la tarea (o el recurso) no existe.
- `429 Too Many Requests`: se supero el rate limit de 100 peticiones por minuto.
- `500 Internal Server Error`: error interno, se recomienda reintentar con
  backoff exponencial.
