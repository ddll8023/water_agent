"""Agent 服务常量定义"""

MAX_SUMMARY_LEN = 50000
RECURSION_LIMIT = 120
TIMEOUT_SECONDS = 600
RECENT_MESSAGE_COUNT = 10

# === LLM 重试 ===
LLM_RETRY_MAX_ATTEMPTS = 3          # 最大重试次数（含首次）
LLM_RETRY_MIN_WAIT = 2.0            # 首次退避等待（秒）
LLM_RETRY_MAX_WAIT = 10.0           # 最大退避等待（秒）
LLM_RETRY_TIMEOUT = 120             # 单次 LLM 调用超时（秒）

# === 健康探针 ===
HEALTH_PROBE_INTERVAL_MINUTES = 60      # 探针执行间隔（分钟）
HEALTH_ALERT_FAILURE_THRESHOLD = 3      # 失败次数阈值
HEALTH_ALERT_WINDOW_MINUTES = 120       # 统计时间窗口（分钟）
