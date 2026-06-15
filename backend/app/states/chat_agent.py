"""M4 智能问答 Agent 状态定义"""

from langgraph.graph import MessagesState


class ChatAgentState(MessagesState):
    collected_context: dict | None
    progress_snapshot: list | None
    error: str | None
