from fastapi import APIRouter, Depends, Body
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import success, error
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.utils.exception import ServiceException
from app.schemas import user as schemas_user
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["认证登录"])


@router.post("/login", response_model=ApiResponse[schemas_user.LoginResponse])
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    login_request: schemas_user.LoginRequest = Body(...),
):
    """登录"""
    try:
        login_response = await auth_service.login(db, login_request)
        return success(login_response)
    except ServiceException as e:
        return error(e.code, e.message)


@router.post("/register", response_model=ApiResponse[schemas_user.RegisterResponse])
async def register(
    db: Annotated[AsyncSession, Depends(get_db)],
    register_request: schemas_user.RegisterRequest = Body(...),
):
    """注册"""
    try:
        register_response = await auth_service.register(db, register_request)
        return success(register_response)
    except ServiceException as e:
        return error(e.code, e.message)
