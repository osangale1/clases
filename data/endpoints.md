# Endpoints disponibles

- `GET /tasks`: lista las tareas del usuario autenticado. Soporta el query
  param `status` (pendiente, en_progreso, completada).
- `POST /tasks`: crea una tarea nueva. Requiere `titulo` (string) y admite
  `descripcion` (string, opcional).
- `PATCH /tasks/{id}`: actualiza el estado o la descripcion de una tarea.
- `DELETE /tasks/{id}`: elimina una tarea.

El limite de uso (rate limit) es de 100 peticiones por minuto por API key.
Si se supera, la API responde 429 Too Many Requests.
