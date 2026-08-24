# Pipeline de Extraccion de Entidades Tecnicas

Pre-entrega 2. Recibe un parrafo de texto crudo (log de error, descripcion de
arquitectura, etc) y devuelve un objeto validado con Pydantic: tecnologias
mencionadas, nivel de criticidad y un resumen tecnico corto.

## Estructura

- `schemas.py`: modelo Pydantic `EntidadesTecnicas` (tecnologias, nivel_de_criticidad, resumen_tecnico).
- `chain.py`: `ChatPromptTemplate` + `model.with_structured_output()` armados con LCEL,
  mas la logica de reintento (`.with_retry()`) y la funcion async `process_text()`.
- `test_pipeline.py`: mini-script de prueba, corre un texto claro y uno ambiguo.

## Instalacion

Requiere Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

```bash
cp .env.example .env
```

Variables (`.env`):

- `LLM_PROVIDER`: `anthropic` o `openai` (default `anthropic`).
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`: si usas Anthropic.
- `OPENAI_API_KEY` / `OPENAI_MODEL`: si usas OpenAI.

## Uso

```bash
python test_pipeline.py
```

## Como funciona

1. `schemas.py` define el contrato de salida con Pydantic (incluye una
   validacion propia: `tecnologias` no puede quedar vacia).
2. `chain.py` arma el prompt con `ChatPromptTemplate` (el texto y las
   instrucciones de formato entran como variables, no hardcodeadas con f-strings).
3. Se usa `model.with_structured_output(EntidadesTecnicas, include_raw=True)`
   para que el LLM devuelva el objeto ya tipado. Con `include_raw=True` tambien
   llega el `finish_reason`/`stop_reason` original y el error de parseo si lo hubo.
4. `revisar_respuesta()` chequea eso antes de dar la respuesta por buena: si el
   modelo corto la respuesta por tokens, o si el JSON no valido, tira
   `RespuestaIncompletaError`.
5. `cadena.with_retry(...)` reintenta hasta 3 veces cuando salta esa excepcion.
6. `process_text(texto)` corre todo con `.ainvoke()` y deja logs de cada paso
   (parseo ok, reintento, etc).

## Ejemplo de salida esperada

Dado un log de error como:

```
[ERROR] Timeout conectando a PostgreSQL (pool agotado, 200/200 conexiones activas).
La cache en Redis esta funcionando bien pero no alcanza a absorber toda la carga.
El servicio corre en FastAPI detras de un Nginx.
```

El pipeline devuelve algo asi:

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con cache en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```

## Prueba de estres

`test_pipeline.py` tambien manda un texto bien ambiguo ("el sistema tuvo un
problema ayer, no se bien que paso, algo con la base de datos") para ver si
el modelo se las arregla igual o si el pipeline termina fallando despues de
los 3 reintentos.
