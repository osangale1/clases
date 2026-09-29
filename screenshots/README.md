Capturas pendientes (necesitan Redis + API + LangSmith/Phoenix corriendo con datos reales):

- traza de una ejecucion completa en el dashboard
- costo por ejecucion de las 5 peticiones concurrentes
- latencia p95 de esa corrida

Pasos: levantar todo (`docker compose up`), correr `python scripts/prueba_carga.py`,
y sacar las capturas del dashboard de LangSmith o Phoenix.
