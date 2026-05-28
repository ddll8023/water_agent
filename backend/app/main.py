from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers import roles as roles_router
from app.routers import reservoir as reservoir_router
from app.routers import stations as stations_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

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


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
