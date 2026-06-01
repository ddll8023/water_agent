from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.schemas.response import ErrorCode
from app.utils.exception import ServiceException

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL, echo=settings.DEBUG, pool_size=10
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def commit_or_rollback(db: AsyncSession):
    """提交当前事务，失败时回滚并转换为业务异常。"""
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise ServiceException(ErrorCode.INTERNAL_ERROR, "操作失败") from e


def get_background_db_session():
    """
    获取后台任务数据库会话
    用于 BackgroundTasks.add_task() 场景
    """
    return async_session()
