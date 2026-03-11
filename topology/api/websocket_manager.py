"""
WebSocket Manager for Real-time Progress Updates

Manages WebSocket connections for streaming operation progress
to connected clients (browser).
"""

from typing import Dict, List, Any
from fastapi import WebSocket
import asyncio
import json


class ConnectionManager:
    """Manages WebSocket connections for job progress updates."""
    
    def __init__(self):
        # Map of job_id -> list of connected WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Map of job_id -> current status
        self.job_status: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a job."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        
        # Send current status if available
        if job_id in self.job_status:
            await websocket.send_json(self.job_status[job_id])
    
    def disconnect(self, job_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def broadcast(self, job_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a job."""
        self.job_status[job_id] = message
        
        if job_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(job_id, conn)
    
    async def send_progress(self, job_id: str, percent: int, message: str):
        """Send a progress update."""
        await self.broadcast(job_id, {
            "type": "progress",
            "percent": percent,
            "message": message
        })
    
    async def send_terminal(self, job_id: str, line: str):
        """Send a terminal output line."""
        await self.broadcast(job_id, {
            "type": "terminal",
            "line": line
        })
    
    async def send_step(self, job_id: str, current: int, total: int, name: str):
        """Send a step update."""
        await self.broadcast(job_id, {
            "type": "step",
            "current": current,
            "total": total,
            "name": name
        })
    
    async def send_complete(self, job_id: str, success: bool, result: Any = None):
        """Send completion status."""
        await self.broadcast(job_id, {
            "type": "complete",
            "success": success,
            "result": result
        })
        
        # Clean up job status after a delay
        await asyncio.sleep(60)
        if job_id in self.job_status:
            del self.job_status[job_id]
    
    async def send_error(self, job_id: str, message: str):
        """Send an error message."""
        await self.broadcast(job_id, {
            "type": "error",
            "message": message
        })
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status for a job."""
        return self.job_status.get(job_id, {"type": "unknown", "message": "Job not found"})
    
    def is_job_active(self, job_id: str) -> bool:
        """Check if a job has active connections."""
        return job_id in self.active_connections and len(self.active_connections[job_id]) > 0


# Global manager instance
manager = ConnectionManager()











