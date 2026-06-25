import logging

from functools import lru_cache


from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_deepseek import ChatDeepSeek
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

    def build_chat_model(
        self,
        model: str = settings.CHAT_MODEL,
        api_key: str = settings.CHAT_API_KEY,
        base_url: str = settings.CHAT_BASE_URL,
        provider: str = "deepseek",
        max_tokens: int | None = None,
        temperature: float | None = None,
        thinking: bool = True,
    ):
        if provider == "deepseek":
            return ChatDeepSeek(
                model=model,
                api_key=api_key,
                base_url=base_url,
                max_tokens=(
                    self.default_chat_max_tokens if max_tokens is None else max_tokens
                ),
                temperature=(
                    self.default_chat_temperature
                    if temperature is None
                    else temperature
                ),
                model_kwargs={
                    "extra_body": {
                        "thinking": {"type": "enabled" if thinking else "disabled"}
                    }
                },
            )
        else:
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                max_tokens=(
                    self.default_chat_max_tokens if max_tokens is None else max_tokens
                ),
                temperature=(
                    self.default_chat_temperature
                    if temperature is None
                    else temperature
                ),
            )


@lru_cache
def get_model_factory():
    return ModelFactory()


get_model = get_model_factory()
