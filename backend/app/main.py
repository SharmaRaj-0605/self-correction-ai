from fastapi import FastAPI

from backend.app.api.routes import router, cache

app = FastAPI(
    title="Self-Correcting Multi-Agent API",
    version="1.0.0",
    description="FastAPI backend for a self-correcting multi-agent AI workflow.",
)

app.include_router(router)


@app.get("/health")
async def health():
    redis_ok = False
    try:
        redis_ok = await cache.ping()
    except Exception:
        pass

    return {
        "status": "ok",
        "cache": "redis" if redis_ok else "in-memory fallback",
    }
