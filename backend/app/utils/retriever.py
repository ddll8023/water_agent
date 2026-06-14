import asyncio

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from app.core.chroma import get_vector_store
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)

_ensemble_retriever: EnsembleRetriever | None = None


async def ensemble_retrieve(query: str, top_k: int = 10):
    """双路 RRF 检索：向量检索 + BM25 加权融合"""
    global _ensemble_retriever

    if _ensemble_retriever is None:
        vector_store = get_vector_store()

        stored = await asyncio.to_thread(
            vector_store.get, include=["documents", "metadatas"]
        )
        all_docs = [
            Document(page_content=t, metadata=m)
            for t, m in zip(stored["documents"], stored["metadatas"])
        ]

        if not all_docs:
            logger.info("ensemble_retrieve: 知识库为空，跳过 RAG 检索")
            return []

        logger.info(f"EnsembleRetriever 初始化完成: total_docs={len(all_docs)}")
        _ensemble_retriever = EnsembleRetriever(
            retrievers=[
                vector_store.as_retriever(search_kwargs={"k": 30}),
                BM25Retriever.from_documents(documents=all_docs, k=30),
            ],
            weights=[0.5, 0.5],
            c=60,
        )

    documents = await _ensemble_retriever.ainvoke(query)

    return documents[:top_k]
