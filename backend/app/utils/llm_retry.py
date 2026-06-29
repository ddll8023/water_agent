"""LLM 调用重试工具：带指数退避和超时的 LLM 调用包装"""

import asyncio
import logging

from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log,
)

from app.constants import agent as constants_agent
from app.utils.logger_config import setup_logger

logger = setup_logger(__name__)

# 可重试错误关键词（小写匹配）
_RETRYABLE_KEYWORDS = [
    "timeout",
    "rate limit",
    "429",
    "503",
    "service unavailable",
    "server error",
    "connection",
    "try again",
    "temporarily",
    "internal server error",
    "bad gateway",
    "service busy",
]

# 不可重试错误关键词（小写匹配）——匹配任意一条立即抛出
_NON_RETRYABLE_KEYWORDS = [
    "authentication",
    "permission",
    "invalid api",
    "api key",
    "authorization",
    "invalid request",
    "not found",
    "insufficient_quota",
]


def _is_retryable(exc: Exception) -> bool:
    """判断是否为可重试的异常

    规则：
    - 匹配 NON_RETRYABLE_KEYWORDS 中任一条 → 不可重试（立即抛出）
    - 匹配 RETRYABLE_KEYWORDS 中任一条 → 可重试
    - 都不匹配 → 可重试（兜底安全策略：宁可重试也不静默丢失）
    """
    msg = str(exc).lower()
    for kw in _NON_RETRYABLE_KEYWORDS:
        if kw in msg:
            return False
    for kw in _RETRYABLE_KEYWORDS:
        if kw in msg:
            return True
    return True


async def ainvoke_with_retry(ainvoke_func, *args, **kwargs):
    """带指数退避重试和超时的 LLM 调用

    Args:
        ainvoke_func: 可调用的异步函数，如 model.ainvoke 或 chain.ainvoke
        *args, **kwargs: 传递给 ainvoke_func 的参数

    重试策略（3 次，含首次）：
      首次失败 → 等待 2s → 重试 → 失败 → 等待 4s → 重试 → 失败 → 等待 8s → 重试 → 失败 → 抛出

    - 不可重试错误（鉴权/参数）立即抛出
    - 单次调用超时 120s
    - 重试耗尽后抛出最后一次异常
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(constants_agent.LLM_RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            min=constants_agent.LLM_RETRY_MIN_WAIT,
            max=constants_agent.LLM_RETRY_MAX_WAIT,
        ),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.WARNING),
    ):
        with attempt:
            return await asyncio.wait_for(
                ainvoke_func(*args, **kwargs),
                timeout=constants_agent.LLM_RETRY_TIMEOUT,
            )
