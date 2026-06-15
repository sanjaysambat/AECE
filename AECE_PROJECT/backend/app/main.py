import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.config import get_settings
from app.db_ops import ensure_tables_created
from app.schemas import HealthResponse
from app.ws_manager import WebSocketManager


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AECE Backend", version="0.1.0")
    app.state.ws_manager = WebSocketManager()

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health():
        return HealthResponse(
            status="ok",
            timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            database_connected=True,
        )

    @app.on_event("startup")
    def on_startup():
        if settings.auto_create_tables:
            ensure_tables_created()
            # Also create app/db tables (ethical_assessments)
            from app.db.base import Base as AppBase
            from app.db.session import engine as app_engine
            import app.db.models  # noqa: F401 - register models
            AppBase.metadata.create_all(bind=app_engine)

    app.include_router(api_router)

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        manager: WebSocketManager = app.state.ws_manager
        await manager.connect(websocket)
        try:
            # Send initial system status snapshot.
            await websocket.send_json(
                {
                    "type": "system_status",
                    "payload": {
                        "status": "ok",
                        "database_connected": True,
                        "websocket_clients_connected": manager.connected_count(),
                        "scoring_mode": "openai_or_heuristic",
                    },
                }
            )

            # Keep listening for optional messages (e.g., weight updates).
            while True:
                msg = await websocket.receive_json()
                if not isinstance(msg, dict):
                    continue

                msg_type = msg.get("type")
                if msg_type == "set_weights":
                    weights = msg.get("weights") or {}
                    await manager.set_weights(websocket, weights)
                    await manager.broadcast({"type": "weights_update", "payload": weights})
                # Ignore unknown messages.
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception:
            await manager.disconnect(websocket)

    return app


app = create_app()

