from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import engine, Base
from app.core.ws_manager import manager
from app.core.redis import close_redis
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
from app.agent.collector import run_collector_agent
from app.agent.analyst import run_analyst_agent
from app.models import alert_rule as models_alert_rule
from app.utils.logger_config import setup_logger
from app.utils.db_init import init_mysql, init_neo4j
from app.routers import documents as documents_router
from app.routers import chat as chat_router
from app.routers import graph as graph_router
from app.routers import graph_admin as graph_admin_router
from app.routers import patrol_log as patrol_log_router

logger = setup_logger(__name__)

# ========= 定时调度器 =========
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库和定时任务，关闭时清理"""
    # ---- startup ----
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # await init_mysql(conn)
    logger.info("数据库表创建完成")

    try:
        await init_neo4j()
    except Exception as e:
        logger.warning("Neo4j 图谱初始化异常（不影响服务启动）: %s", e)

    # Collector Agent：每 10 分钟采集与规则预警
    scheduler.add_job(
        run_collector_agent,
        "interval",
        minutes=10,
        id="collector_agent",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )

    # Analyst Agent：每 6 小时趋势分析
    scheduler.add_job(
        run_analyst_agent,
        "interval",
        hours=6,
        id="analyst_agent",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,
    )
    scheduler.start()

    yield  # 应用运行中

    # ---- shutdown ----
    if scheduler.running:
        scheduler.shutdown(wait=False)

    await close_redis()


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

from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.response import error, success
from app.schemas.common import ErrorCode
from app.utils.exception import ServiceException


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    return JSONResponse(
        status_code=200,
        content=error(code=exc.code, message=exc.message),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理的服务器异常")
    return JSONResponse(
        status_code=200,
        content=error(code=ErrorCode.INTERNAL_ERROR, message="服务器内部错误"),
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
app.include_router(graph_router.router)
app.include_router(graph_admin_router.router)
app.include_router(patrol_log_router.router)


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
