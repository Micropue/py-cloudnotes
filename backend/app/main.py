import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import exc as sa_exc
from app.database import engine
from app.models import Base
from app.config import UPLOAD_DIR
from app.routers import auth, notes, comments, upload, share
from app.websocket.handler import handle_websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 数据库连接重试，解决 Docker 启动时序问题
    for attempt in range(30):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except sa_exc.OperationalError:
            if attempt == 29:
                raise
            await asyncio.sleep(1)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title="云笔记 API",
    description="Markdown 云笔记 + 实时协作系统",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(share.router)
app.include_router(comments.router)
app.include_router(upload.router)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/notes/{note_id}")
async def websocket_note(
    websocket: WebSocket,
    note_id: int,
    token: str = Query(...),
):
    from jose import jwt as jose_jwt
    from app.config import SECRET_KEY, ALGORITHM
    try:
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if not user_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await handle_websocket(
        websocket,
        note_id=note_id,
        user_id=user_id,
        username=username,
        avatar_url=f"https://api.dicebear.com/9.x/initials/svg?seed={username}",
    )
