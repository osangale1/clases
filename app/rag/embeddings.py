import os

from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app import config

TAMANO_LOTE = 50


class GeminiEmbeddings(Embeddings):
    """Embeddings de Gemini (gemini-embedding-2, gratis en el tier gratuito).

    gemini-embedding-2 no acepta task_type y, si se le pasa una lista de textos, devuelve UN solo
    embedding agregado. Por eso cada texto va en su propio Content y la tarea (documento / consulta)
    se indica con el prefijo que pide la documentacion de Google.
    """

    def __init__(self, model: str, dimension: int):
        self.model = model
        self.dimension = dimension
        self._cliente = None

    @property
    def cliente(self) -> genai.Client:
        if self._cliente is None:
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            self._cliente = genai.Client(api_key=api_key)
        return self._cliente

    def _contenidos(self, textos: list[str]) -> list[types.Content]:
        return [types.Content(parts=[types.Part.from_text(text=t)]) for t in textos]

    def _config(self) -> types.EmbedContentConfig:
        return types.EmbedContentConfig(output_dimensionality=self.dimension)

    @staticmethod
    def _como_documento(texto: str) -> str:
        return f"title: none | text: {texto}"

    @staticmethod
    def _como_consulta(texto: str) -> str:
        return f"task: search result | query: {texto}"

    def _extraer(self, respuesta, esperados: int) -> list[list[float]]:
        vectores = [list(e.values) for e in respuesta.embeddings]
        if len(vectores) != esperados:
            raise ValueError(f"Gemini devolvio {len(vectores)} embeddings para {esperados} textos")
        return vectores

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectores = []
        for i in range(0, len(texts), TAMANO_LOTE):
            lote = [self._como_documento(t) for t in texts[i : i + TAMANO_LOTE]]
            respuesta = self.cliente.models.embed_content(
                model=self.model, contents=self._contenidos(lote), config=self._config()
            )
            vectores += self._extraer(respuesta, len(lote))
        return vectores

    def embed_query(self, text: str) -> list[float]:
        respuesta = self.cliente.models.embed_content(
            model=self.model, contents=self._contenidos([self._como_consulta(text)]), config=self._config()
        )
        return self._extraer(respuesta, 1)[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        vectores = []
        for i in range(0, len(texts), TAMANO_LOTE):
            lote = [self._como_documento(t) for t in texts[i : i + TAMANO_LOTE]]
            respuesta = await self.cliente.aio.models.embed_content(
                model=self.model, contents=self._contenidos(lote), config=self._config()
            )
            vectores += self._extraer(respuesta, len(lote))
        return vectores

    async def aembed_query(self, text: str) -> list[float]:
        respuesta = await self.cliente.aio.models.embed_content(
            model=self.model, contents=self._contenidos([self._como_consulta(text)]), config=self._config()
        )
        return self._extraer(respuesta, 1)[0]


def get_embeddings() -> Embeddings:
    if config.EMBEDDING_PROVIDER == "google":
        return GeminiEmbeddings(config.EMBEDDING_MODEL, config.EMBEDDING_DIMENSION)

    if config.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddings(model=config.EMBEDDING_MODEL)

    raise ValueError(f"proveedor de embeddings no soportado: {config.EMBEDDING_PROVIDER}")
