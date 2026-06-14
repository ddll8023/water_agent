"""Agent 工作流状态定义"""

from enum import IntEnum, Enum
from typing import TypedDict
from pydantic import BaseModel


class PatrolStatus(IntEnum):
    """采集管道执行状态"""

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


class ReportStatus(IntEnum):
    """Report Generator 执行状态"""

    SUCCESS = 0
    NO_DATA = 1
    FAILED = 2


class ReportType(str, Enum):
    DAILY = "daily"
    QUARTERLY = "quarterly"
    EVENT = "event"




