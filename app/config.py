import os

from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
JOB_TTL_SEGUNDOS = int(os.environ.get("JOB_TTL_SEGUNDOS", "86400"))

INDEX_NAME = os.environ.get("INDEX_NAME", "curso-rag-index")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "documentacion-tecnica")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")

EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "google").lower()
_EMBEDDING_POR_DEFECTO = {"google": ("gemini-embedding-2", 768), "openai": ("text-embedding-3-small", 1536)}
_modelo_def, _dimension_def = _EMBEDDING_POR_DEFECTO.get(EMBEDDING_PROVIDER, ("", 0))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", _modelo_def)
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", _dimension_def))

CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "60"))
TOP_K = int(os.environ.get("TOP_K", "5"))

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "google").lower()
GOOGLE_MODEL = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

MAX_PASOS = int(os.environ.get("MAX_PASOS", "6"))
RECURSION_LIMIT = int(os.environ.get("RECURSION_LIMIT", "25"))

PHOENIX_ENABLED = os.environ.get("PHOENIX_ENABLED", "false").lower() == "true"
PHOENIX_ENDPOINT = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
PHOENIX_PROJECT = os.environ.get("PHOENIX_PROJECT_NAME", "sistema-final")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
