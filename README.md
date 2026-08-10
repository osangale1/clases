# Unified Async LLM Client

Cliente async simple para hablar con OpenAI y Anthropic bajo la misma interfaz,
con soporte de streaming y validacion de datos con Pydantic.

## Estructura

- `schemas.py`: modelos Pydantic (`ChatMessage`, `ModelConfig`, `ModelResponse`).
- `clients.py`: `BaseLLMClient` (clase base), `OpenAIClient`, `AnthropicClient`
  y `AsyncLLMManager` (elige el proveedor).
- `main.py`: script de prueba (modo normal y streaming).

## Instalacion

Requiere Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Copia `.env.example` a `.env` y pon tus API keys:

```bash
cp .env.example .env
```

Variables:

- `OPENAI_API_KEY`: API key de OpenAI (opcional, solo si vas a probar OpenAI).
- `ANTHROPIC_API_KEY`: API key de Anthropic (opcional, solo si vas a probar Anthropic).
- `OPENAI_MODEL`: modelo de OpenAI a usar (default `gpt-4o-mini`).
- `ANTHROPIC_MODEL`: modelo de Anthropic a usar (default `claude-opus-5`).

Si alguna de las dos API keys no esta configurada, `main.py` simplemente
se salta la prueba de ese proveedor.

## Uso

```bash
python main.py
```

Esto hace una pregunta corta ("¿Qué es la entropía?") a cada proveedor
configurado, primero en modo normal y despues en modo streaming (token por token).

## Manejo de errores

Si la API key es invalida, hay un error de red o se llega al limite de tasa,
el cliente no lanza la excepcion hacia arriba: la captura y devuelve un
`ModelResponse` con el error dentro de `content`, tanto en modo normal como
en streaming.
