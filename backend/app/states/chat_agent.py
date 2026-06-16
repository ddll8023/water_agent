"""M4 智能问答 Agent 状态定义"""

from langgraph.graph import MessagesState


class ChatAgentState(MessagesState):
    progress_snapshot: list | None = None
    error: str | None = None
