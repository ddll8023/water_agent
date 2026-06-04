import logging

from functools import lru_cache


from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelFactory:
    def __init__(self):
        self.default_chat_max_tokens = 32768
        self.default_chat_temperature = 0

        self.embedding_model = DashScopeEmbeddings(
            model=settings.EMBEDDING_MODEL,
            dashscope_api_key=settings.EMBEDDING_API_KEY,
        )

        self.chat_one_model = self.build_chat_model(
            model=settings.CHAT_ONE_MODEL,
            api_key=settings.CHAT_ONE_API_KEY,
            base_url=settings.CHAT_ONE_BASE_URL,
        )
        # self.chat_two_model = self.build_chat_model(
        #     model=settings.CHAT_TWO_MODEL,
        #     api_key=settings.CHAT_TWO_API_KEY,
        #     base_url=settings.CHAT_TWO_BASE_URL,
        # )

    def build_chat_model(
        self,
        model: str,
        api_key: str,
        base_url: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=(
                self.default_chat_max_tokens if max_tokens is None else max_tokens
            ),
            temperature=(
                self.default_chat_temperature if temperature is None else temperature
            ),
        )


@lru_cache
def get_model_factory():
    return ModelFactory()


get_model = get_model_factory()
