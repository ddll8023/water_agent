"""聊天对话路由（SSE 流式）"""

from fastapi import APIRouter, Depends
from typing import Annotated
from fastapi.responses import StreamingResponse
from app.core.security import require_role
from app.core.security import get_current_user
from app.schemas import auth as schemas_auth
from app.schemas import chat as schemas_chat
from app.services import chat as service_chat

router = APIRouter(prefix="/api/v1/chat", tags=["智能问答"])


@router.post(
    "", dependencies=[Depends(require_role("admin", "user"))], summary="流式对话"
)
async def chat_stream(
    chat_request: schemas_chat.ChatRequest,
    current_user: Annotated[
        schemas_auth.ValidateTokenUserItem, Depends(get_current_user)
    ],
):
    """SSE 流式对话"""
    return StreamingResponse(
        service_chat.chat(current_user.user_id, chat_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
