# Pipeline de Extraccion de Entidades Tecnicas

Pre-entrega 2. Recibe un texto y devuelve un JSON validado con las
tecnologias mencionadas, el nivel de criticidad y un resumen.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Copiar `.env.example` a `.env` y completar las API keys. `LLM_PROVIDER`
puede ser `anthropic` u `openai`.

## Uso

```bash
python test_pipeline.py
```

## Ejemplo de salida

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con cache en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```
