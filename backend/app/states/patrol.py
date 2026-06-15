"""采集管道执行状态定义"""

from enum import IntEnum


class PatrolStatus(IntEnum):
    """采集管道执行状态"""

    SUCCESS = 0
    PARTIAL = 1
    FAILED = 2
    NO_DATA = 3
