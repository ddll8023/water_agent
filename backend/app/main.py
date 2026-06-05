from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import engine, Base
from app.core.ws_manager import manager
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers import roles as roles_router
from app.routers import reservoir as reservoir_router
from app.routers import stations as stations_router
from app.routers import indicators as indicators_router
from app.routers import monitoring as monitoring_router
from app.routers import dashboard as dashboard_router
from app.routers import alerts as alerts_router
from app.routers import alert_rules as alert_rules_router
from app.services.monitoring import collect_water_quality_data
from app.models import alert_rule as models_alert_rule
from app.utils.logger_config import setup_logger
from app.utils.db_init import init_db
from app.routers import documents as documents_router
from app.routers import chat as chat_router

logger = setup_logger(__name__)

# ========= 定时调度器 =========
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库和定时任务，关闭时清理"""
    # ---- startup ----
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # await init_db(conn)
    logger.info("数据库表创建完成")

    # 启动后立即执行一次采集
    await collect_water_quality_data()

    # 每10分钟定时采集（从第二次开始计时）
    scheduler.add_job(
        collect_water_quality_data,
        "interval",
        minutes=10,
        id="collect_water_quality",
        replace_existing=True,
    )
    scheduler.start()

    yield  # 应用运行中

    # ---- shutdown ----
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(roles_router.router)
app.include_router(reservoir_router.router)
app.include_router(stations_router.router)
app.include_router(indicators_router.router)
app.include_router(monitoring_router.router)
app.include_router(dashboard_router.router)
app.include_router(alerts_router.router)
app.include_router(alert_rules_router.router)
app.include_router(documents_router.router)
app.include_router(chat_router.router)


@app.websocket("/ws/alerts")
async def alert_websocket(ws: WebSocket):
    """实时预警推送 WebSocket"""
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
