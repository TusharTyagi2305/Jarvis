from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jarvis.config import settings
from jarvis.api.routes import router as api_router

app = FastAPI(
    title="JARVIS Personal Desktop AI Assistant",
    version="0.1.0",
    description="REST API interface for JARVIS desktop agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

from fastapi import WebSocket, WebSocketDisconnect
from jarvis.api.websocket import ws_manager
from jarvis.api.events import StateEvent

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Emit initial state on connection
    await websocket.send_json(StateEvent(state="IDLE").model_dump())
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping/pong or command messages
            if data.strip() == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/health")
@app.get("/api/health")
async def health_check_root():
    from jarvis.diagnostics import StartupDiagnostics
    diag = StartupDiagnostics.check_environment()
    return {
        "status": "healthy",
        "version": settings.jarvis_version,
        "subsystems": diag
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "JARVIS Personal Desktop Agent",
        "version": settings.jarvis_version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
