from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.auth import router as auth_router
from app.api.webhook import router as webhook_router
from app.db.clickhouse import init_clickhouse
from app.db.postgres import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_clickhouse()
    yield
    await engine.dispose()


app = FastAPI(
    title="Spend Metrics API",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(auth_router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
