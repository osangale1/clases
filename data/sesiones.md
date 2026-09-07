# Sesiones

Cuando se hacen muchas peticiones seguidas al mismo servidor, conviene usar
una sesion en vez de llamadas sueltas. La sesion reutiliza la conexion TCP
por debajo (connection pooling), lo que mejora bastante la performance.

Ademas, los headers, cookies y la autenticacion configurados en la sesion se
mantienen entre peticiones, asi no hay que repetirlos en cada llamada.

Es buena practica cerrar la sesion al terminar (o usarla con un bloque
`with`), para liberar las conexiones abiertas.
