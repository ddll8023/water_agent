from fastapi import APIRouter, Depends, Body
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException
from app.schemas import auth as schemas_auth
from app.services import auth as service_auth
from app.core.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证登录"])


@router.post(
    "/login", response_model=ApiResponse[schemas_auth.LoginResponse], description="登录"
)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    login_request: schemas_auth.LoginRequest = Body(...),
):
    """登录"""
    try:
        login_response = await service_auth.login(db, login_request)
        return success(login_response)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post(
    "/register",
    response_model=ApiResponse[schemas_auth.RegisterResponse],
    description="注册",
)
async def register(
    db: Annotated[AsyncSession, Depends(get_db)],
    register_request: schemas_auth.RegisterRequest = Body(...),
):
    """注册"""
    try:
        register_response = await service_auth.register(db, register_request)
        return success(register_response)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post("/logout", response_model=ApiResponse, description="退出登录")
async def logout():
    """退出登录"""
    try:
        return success(await service_auth.logout())
    except ServiceException as e:
        return error(e.code, e.message)


@router.get(
    "/me",
    response_model=ApiResponse[schemas_auth.GetCurrentUserDetailResponse],
    description="获取当前用户详情",
)
async def get_current_user_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_item: Annotated[schemas_auth.ValidateTokenUserItem, Depends(get_current_user)],
):
    """获取当前用户详情"""
    try:
        current_user_detail = await service_auth.get_current_user_detail(db, user_item)
        return success(current_user_detail)
    except ServiceException as e:
        return error(e.code, e.message)
