from langchain_chroma import Chroma
from app.core.config import settings
from app.utils.model_factory import get_model



_vector_store = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=get_model.embedding_model,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
    return _vector_store