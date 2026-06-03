"""WebSocket 连接管理器"""

from fastapi import WebSocket


class ConnectionManager:
    """管理 WebSocket 连接池，支持广播"""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.discard(ws)

    async def broadcast(self, message: dict):
        """向所有在线客户端广播 JSON 消息，自动移除断开连接"""
        dead: set[WebSocket] = set()
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.add(conn)
        for conn in dead:
            self.active_connections.discard(conn)


manager = ConnectionManager()
