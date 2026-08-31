# Despliegue

El servicio se distribuye como imagen Docker (`tasks-api:latest`). Escucha
por defecto en el puerto 8080.

Variables de entorno requeridas:

- `DATABASE_URL`: string de conexion a PostgreSQL.
- `API_KEY_SECRET`: semilla usada para generar y validar las API keys.

Para levantarlo en local:

```bash
docker run -p 8080:8080 -e DATABASE_URL=... -e API_KEY_SECRET=... tasks-api:latest
```

No se versiona ningun archivo `.env` con credenciales reales.
