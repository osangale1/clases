# Autenticacion

Todas las peticiones a la API deben incluir el header `X-API-Key` con una
clave valida. Las claves se generan desde el panel de administracion y
expiran a los 90 dias.

Si el header falta o la clave es invalida, la API responde con un error
401 Unauthorized.

No existe autenticacion por usuario y contraseña, solo por API key.
