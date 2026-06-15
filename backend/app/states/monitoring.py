"""监测数据处理产出统计 DTO"""

from pydantic import BaseModel


class ProcessResult(BaseModel):
    """process_and_save_data 产出统计"""

    station_count: int
    record_count: int
    pending_alerts: list[dict]
    cached_records: list[dict]
    error_info: str | None
