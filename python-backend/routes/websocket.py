from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

from utils.logger import logger

router = APIRouter()

# Store active WebSocket connections per project
# Key: project_id, Value: set of WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept a new WebSocket connection for a project"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()

        self.active_connections[project_id].add(websocket)
        logger.info(f"WebSocket connected for project {project_id}. Total connections: {len(self.active_connections[project_id])}")

    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
            logger.info(f"WebSocket disconnected for project {project_id}")

    async def broadcast_to_project(self, project_id: str, message: dict):
        """Broadcast a message to all connections for a project"""
        if project_id not in self.active_connections:
            return

        disconnected = set()
        message_str = json.dumps(message)

        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            self.active_connections[project_id].discard(ws)

        if disconnected:
            logger.info(f"Cleaned up {len(disconnected)} disconnected sockets for project {project_id}")

    def get_connection_count(self, project_id: str) -> int:
        """Get number of active connections for a project"""
        return len(self.active_connections.get(project_id, set()))


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project updates"""
    await manager.connect(websocket, project_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for ping/pong
                )

                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
        manager.disconnect(websocket, project_id)


async def notify_file_change(project_id: str, file_path: str, operation: str, agent_type: str = None):
    """Notify all connected clients about a file change"""
    message = {
        "type": "file_change",
        "path": file_path,
        "operation": operation,
        "agent_type": agent_type,
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast_to_project(project_id, message)
    logger.info(f"Broadcasted file change notification: {operation} {file_path}")


async def notify_file_operations_complete(project_id: str, results: list):
    """Notify clients that file operations have completed"""
    message = {
        "type": "file_operations_complete",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast_to_project(project_id, message)
    logger.info(f"Broadcasted file operations complete: {len(results)} operations")


@router.get("/connections/{project_id}")
async def get_connection_count(project_id: str):
    """Get the number of active WebSocket connections for a project"""
    count = manager.get_connection_count(project_id)
    return {"project_id": project_id, "connections": count}
