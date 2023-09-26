# ws_manager.py
from typing import Dict, Set
from fastapi import WebSocket

class WSManager_status:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        self.active_connections.setdefault("logs", set()).add(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections["logs"].remove(websocket)

    async def send_log_message(self, message: str):
        try:
            print(f"Active connections: {self.active_connections}")
            print(f"Sending message: {message}")
            for ws in self.active_connections.get("logs", []):
                await ws.send_json({"type": "log", "message": message})
            print("Message sent successfully")
        except Exception as e:
            print(f"Error while sending message: {e}")
        

ws_manager_status = WSManager_status()
