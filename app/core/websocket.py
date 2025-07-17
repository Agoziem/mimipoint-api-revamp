
from typing import Dict, List
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect

# In-memory connection manager (simple version)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Dict[str, List[WebSocket]]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket, context: str):
        """Connect user to a specified context (e.g., 'dashboard', 'notifications')."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        if context not in self.active_connections[user_id]:
            self.active_connections[user_id][context] = []

        self.active_connections[user_id][context].append(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket, context: str):
        """Disconnect a user from a specific context."""
        if user_id in self.active_connections and context in self.active_connections[user_id]:
            self.active_connections[user_id][context].remove(websocket)
            if not self.active_connections[user_id][context]:
                del self.active_connections[user_id][context]
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

    async def send_notification(self, user_id: UUID, context: str, data: dict):
        """Send message to a specific context (e.g., 'notifications') of a user."""
        if user_id in self.active_connections and context in self.active_connections[user_id]:
            for connection in self.active_connections[user_id][context]:
                await connection.send_json(data)
