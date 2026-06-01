"""监测数据路由（预留）"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/monitoring", tags=["监测数据"])

# 模拟接口已移除，改为定时采集任务
# 改为定时采集任务，参见 app/services/monitoring.py
