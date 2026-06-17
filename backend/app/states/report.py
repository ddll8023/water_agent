"""Report Generator 报告生成状态与类型定义"""

from enum import IntEnum, Enum


class ReportStatus(IntEnum):
    """Report Generator 执行状态"""

    SUCCESS = 0
    NO_DATA = 1
    FAILED = 2


class ReportType(str, Enum):
    """报告类型（值类型为字符串，故使用 str, Enum 而非 IntEnum）"""

    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    EVENT = "event"
