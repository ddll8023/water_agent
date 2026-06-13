from enum import IntEnum
from typing import TypedDict

from pydantic import BaseModel


class PatrolStatus(IntEnum):
    """巡检执行状态（与 patrol_log.status 字段一致）"""

    SUCCESS = 0  # 成功
    PARTIAL = 1  # 部分失败（有错误但有记录入库）
    FAILED = 2  # 失败
    NO_DATA = 3  # 无数据


class ProcessResult(BaseModel):
    """Node2 处理入库的产出统计"""

    station_count: int
    record_count: int
    pending_alerts: list[
        dict
    ]  # 待判定的预警数据[{indicator_id, reservoir_id, value, record_time}]
    cached_records: list[dict]
    error_info: str | None = None


class PatrolState(TypedDict):
    """Patrol 巡检预警工作流状态"""

    status: PatrolStatus | None  # None=初始
    raw_data: dict | None
    process_result: ProcessResult | None
    target_reservoir_id: int | None
    patrol_log_id: int | None
    error: str | None
    start_time: str | None
    duration_ms: int | None
    should_analyze: bool | None  # None=未判断  True=满足12h条件  False=不满足
    analysis_summary: str | None
    supplementary_alerts: list | None
