"""Analyst Agent 趋势分析工作流状态定义"""

from enum import IntEnum
from typing import TypedDict
from langgraph.graph import MessagesState


class AnalystStatus(IntEnum):
    """Analyst Agent 执行状态"""

    SUCCESS = 0
    PARTIAL = 1
    FAILED = 2
    NO_DATA = 3


class AnalystState(TypedDict):
    """Analyst Agent 趋势分析工作流状态"""

    status: AnalystStatus | None
    period_start: str | None
    period_end: str | None
    reservoirs_data: list | None
    features: list | None
    llm_output: dict | None
    supplementary_alert_ids: dict[int, list[int]] | None
    analysis_ids: list[int] | None
    error: str | None
    start_time: str | None
    duration_ms: int | None


class ReActAnalystState(MessagesState):
    """ReAct Agent 趋势分析工作流状态"""

    status: AnalystStatus | None
    period_start: str | None
    period_end: str | None
    reservoirs_data: list | None
    features: list | None
    analysis_result: dict | None
    supplementary_alert_ids: dict[int, list[int]] | None
    analysis_ids: list[int] | None
    error: str | None
    start_time: str | None
    duration_ms: int | None
