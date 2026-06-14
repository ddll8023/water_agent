"""Agent 工作流状态定义"""

from enum import IntEnum
from typing import TypedDict
from pydantic import BaseModel


class PatrolStatus(IntEnum):
    """Collector Agent 执行状态"""

    SUCCESS = 0
    PARTIAL = 1
    FAILED = 2
    NO_DATA = 3


class ProcessResult(BaseModel):
    """process_and_save_data 产出统计"""

    station_count: int
    record_count: int
    pending_alerts: list[dict]
    cached_records: list[dict]
    error_info: str | None


class AnalystStatus(IntEnum):
    """Analyst Agent 执行状态"""

    SUCCESS = 0
    PARTIAL = 1
    FAILED = 2
    NO_DATA = 3


class PatrolState(TypedDict):
    """Collector Agent 巡检预警工作流状态"""

    status: PatrolStatus | None
    raw_data: dict | None
    process_result: ProcessResult | None
    target_reservoir_id: int | None
    patrol_log_id: int | None
    error: str | None
    start_time: str | None
    duration_ms: int | None


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



