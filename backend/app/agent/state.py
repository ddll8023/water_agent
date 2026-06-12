from typing import TypedDict


class ProcessResult(TypedDict):
    """Node2 处理入库的产出统计"""
    station_count: int
    record_count: int
    pending_alerts: list[dict]  # 待判定的预警数据[{indicator_id, reservoir_id, value, record_time}]
    cached_records: list[dict]
    error_info: str | None


class PatrolState(TypedDict):
    """Patrol 巡检预警工作流状态"""
    status: int | None  # None=初始 0=成功 1=部分失败 2=失败 3=无数据
    raw_data: dict | None
    process_result: ProcessResult | None
    patrol_log_id: int | None
    error: str | None
    start_time: str | None
    duration_ms: int | None
    alert_count: int | None
    should_analyze: bool | None  # None=未判断  True=满足12h条件  False=不满足
    analysis_summary: str | None
    supplementary_alerts: list | None
