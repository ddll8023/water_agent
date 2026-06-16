import asyncio

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from app.core.chroma import get_vector_store
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)

_ensemble_retriever: EnsembleRetriever | None = None

# LLM 工具调用传的是字符串（"standard"/"case"/"sop"），Chroma 中存的是 int（0/1/2）
_DOC_TYPE_MAP: dict[str, int] = {
    "standard": 0,
    "case": 1,
    "sop": 2,
}


async def invalidate_retriever():
    """Chroma 数据变更后调用，下次检索时自动重建 EnsembleRetriever"""
    global _ensemble_retriever
    _ensemble_retriever = None
    logger.info("EnsembleRetriever 已标记失效，下次检索将重建")


async def ensemble_retrieve(query: str, top_k: int = 10, doc_type: str | None = None):
    """双路 RRF 检索：向量检索 + BM25 加权融合"""
    vector_store = get_vector_store()

    # 指定 doc_type 时：先过滤，再在子集内做向量检索，不经过 BM25
    if doc_type:
        dt_int = _DOC_TYPE_MAP.get(doc_type)
        if dt_int is None:
            logger.warning(f"ensemble_retrieve: 未知 doc_type={doc_type}")
            return []
        docs_with_scores = await vector_store.asimilarity_search_with_relevance_scores(
            query, k=top_k, filter={"doc_type": dt_int}
        )
        documents = [d for d, _ in docs_with_scores]
        logger.info(f"ensemble_retrieve(doc_type={doc_type}): 命中 {len(documents)} 条")
        return documents

    # 不指定 doc_type 时：走全量双路 RRF 融合
    global _ensemble_retriever
    if _ensemble_retriever is None:
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
